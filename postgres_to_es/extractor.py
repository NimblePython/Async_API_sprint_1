"""
Модуль для считывания данных из источника.
Источник - БД в 'PostgreSQL'.
"""
import logging
import time
import psycopg2
import psycopg2.extensions as pg_extensions
import statemanager
import configparser

from models import FilmworkModel, PersonModel, GenreModel, Schema
from transform import Transform
from psycopg2.extensions import connection as _connection
from datetime import datetime
from backoff_dec import backoff


class LoggingCursor(pg_extensions.cursor):
    def execute(self, sql, args=None):
        logger = logging.getLogger('sql_debug.log')
        logger.info(self.mogrify(sql, args))

        try:
            psycopg2.extensions.cursor.execute(self, sql, args)
        except Exception as e:
            logger.exception("%s: %s" % (e.__class__.__name__, e))
            raise


class Extractor:
    # ключ - дата персонажа, успешно записанного в ЭС вместе со всеми его фильмами в индексе: movies
    PERSON_MODIFIED_KEY = '_pers_modified'

    # ключ - дата жанра, успешно записанного в ЭС вместе со всеми его фильмами в индексе: movies
    GENRE_MODIFIED_KEY = '_gen_modified'

    # ключ отслеживающий дату фильма, в котором произошли изменения и успешно записанного в ЭС в индекс: movies
    FILM_MODIFIED_KEY = '_film_modified'

    # ключ, похожий на PERSON_MODIFIED_KEY, но этот необходим для контроля статуса записи в индексе: persons
    PERSON_IN_FILMS_MODIFIED_KEY = '_pers_in_films_modified'

    # ключ, похожий на GENRE_MODIFIED_KEY, но этот необходим для контроля статуса записи в индексе: genres
    GENRE_IN_FILMS_MODIFIED_KEY = '_gen_in_films_modified'

    cnt_load = 0
    cnt_part_load = 0
    cnt_successes = 0

    def __init__(self, connection: _connection, dsl: dict):
        self.conn = connection
        self.es_host = dsl['host']
        self.es_port = int(dsl['port'])

        self.films_to_es = []

        json_storage = statemanager.JsonFileStorage('conditions.txt')
        self.manager = statemanager.State(json_storage)

        # значения по умолчанию
        self.chunk = 1000
        self.fetch_size = 100

        # значения из settings.ini если они там заданы, иначе - по умолчанию
        # TODO: Поменять на рydantic config
        config = configparser.ConfigParser()  # создаём объект парсера конфига
        config.read('settings.ini')
        self.chunk = int(config['Extractor']['chunk_size'])
        self.fetch_size = int(config['Extractor']['fetch_size'])
        self.pause = int(config['Extractor']['pause_between'])

        logging.info(f'Размер кипы: {self.chunk}')
        logging.info(f'Размер порций fetch: {self.fetch_size}')

    def get_query(self, model: Schema):
        query = f"""
                SELECT id, updated_at
                FROM content.{model.table}
                WHERE updated_at > '{model.modified}'
                ORDER BY updated_at
                LIMIT {self.chunk};
                """
        return query

    @backoff()
    def query_exec(self, cursor, query_to_exec):
        logging.debug(query_to_exec)
        cursor.execute(query_to_exec)
        return cursor

    def get_key_value(self, key: str) -> str:
        """ Считываем ключ и возвращаем значение переменной
        Если такого ключа нет то устанавливаем его в дефолтное значение
        :param key:
        :return:
        """
        value = datetime(1895, 12, 28, 0, 0).strftime('%Y-%m-%d %H:%M:%S')  # дата рождения синематографа
        if date := self.manager.get_state(key):
            value = date
            logging.info(f'Ключ {key} считан из хранилища: {value}')
        else:
            self.manager.set_state(key, value)
            logging.info(f'Ключ {key} создан и записан в хранилище со значением {value}')

        return value

    @staticmethod
    def get_date_from_chunk_and_cut(chunk: list):
        date = chunk[-1][1].strftime('%Y-%m-%d %H:%M:%S.%f%z')
        # вычищаем все даты, так как сохранили нужную
        chunk = [itm[0] for itm in chunk]
        return date, chunk

    def get_data_and_send_to_es(self, model: Schema, entities: list):
        query = ""
        if model.table == 'person':
            query = \
                f"""
                    SELECT row_to_json(info) as view
                    FROM (
                        SELECT 
                            p.id uuid, 
                            p.full_name,
                            (
                                SELECT 
                                    json_agg(film_group)
                                FROM 
                                (
                                    SELECT 
                                        pfw.film_work_id uuid,
                                        json_agg(pfw."role") roles 
                                    FROM 
                                        content.person_film_work pfw
                                    WHERE 
                                        pfw.person_id = p.id
                                    GROUP BY 1
                                ) film_group
                            ) as films
                        FROM
                            content.person p
                            LEFT JOIN content.person_film_work tfw ON tfw.person_id = p.id
                        WHERE
                            tfw.person_id in ({', '.join(f"'{el}'" for el in entities)})
                        GROUP BY 1
                        LIMIT {self.chunk}
                    ) info;
                """
        elif model.table == 'genre':
            query = \
                f"""
                    SELECT row_to_json(info) as view
                    FROM (      
                        SELECT 
                            g.id uuid,
                            g."name",
                            g.description
                        FROM 
                            content.genre g
                        WHERE
                            g.id in ({', '.join(f"'{el}'" for el in entities)})
                        LIMIT {self.chunk}
                    ) info;
                """

        with self.conn.cursor() as cur:
            # запрашиваем CHUNK данных, которые связаны с изменениями
            cur = self.query_exec(cur, query)
            # готовим fetch_size кусок UUIN фильмов для ES
            while records := cur.fetchmany(self.fetch_size):
                data_to_elastic = [model.model(**record['view']) for record in records]
                logging.info(f'Вызван для таблицы {model.table}. Данные собраны для индекса ES: {model.es_index}')
                try:
                    # пушим в ES
                    self.push_to_es(data_to_elastic, es_index=model.es_index)
                    # Если запись прошла успешно, то меняем статус
                    if Extractor.cnt_part_load == Extractor.cnt_successes:
                        # Изменяем состояние (дату) для модели от имени которой произошел вызов функции
                        self.manager.set_state(model.key, model.modified)
                        logging.info(f"Изменено состояние для ключа {model.key} в значение {model.modified}")
                except Exception as e:
                    logging.exception('%s: %s' % (e.__class__.__name__, e))

    def get_films_and_send_to_es(self, model: Schema, entities: list):
        # если источник изменений сами фильмы, то формируем один вариант запроса, иначе - другой
        if model.table == 'film_work':
            query = \
                f"""
                SELECT DISTINCT fw.id
                FROM content.film_work fw
                WHERE 
                    fw.id in ({', '.join(f"'{el}'" for el in entities)})
                LIMIT {self.chunk};
                """
        else:
            query = \
                f"""
                SELECT DISTINCT fw.id
                FROM content.film_work fw
                LEFT JOIN 
                    content.{model.table}_film_work tfw ON tfw.film_work_id = fw.id
                WHERE 
                    tfw.{model.table}_id in ({', '.join(f"'{el}'" for el in entities)})
                LIMIT {self.chunk};
                """

        with self.conn.cursor() as cur_films:
            # запрашиваем CHUNK фильмов, которое связано с изменениями
            cur_films = self.query_exec(cur_films, query)
            # готовим fetch_size кусок UUIN фильмов для ES
            while films := cur_films.fetchmany(self.fetch_size):
                self.films_to_es = [record[0] for record in films]
                logging.debug(f'Вызван для {model.table} --- Фильмы собраны для ES:')
                try:
                    # запуск обогатителя: добавит недостающую информацию и запишет в ES
                    self.postgres_enricher()
                    # Если запись прошла успешно, то меняем статус
                    if Extractor.cnt_part_load == Extractor.cnt_successes:
                        # Изменяем состояние (дату) для модели от имени которой произошел вызов функции
                        self.manager.set_state(model.key, model.modified)
                        logging.info(f"Изменено состояние для ключа {model.key} в значение {model.modified}")
                except Exception as e:
                    logging.exception('%s: %s' % (e.__class__.__name__, e))

    def postgres_producer(self):
        # ЗАПУСАЕМ ПРОЦЕСС В БЕСКОНЕЧНОМ ЦИКЛЕ
        is_run = True
        while is_run:
            objects: list[Schema] = []

            logging.info(f"Пауза {self.pause} сек.")
            time.sleep(self.pause)  # пауза между сессиями сканирования БД

            data = self.get_key_value(Extractor.PERSON_MODIFIED_KEY)
            objects.append(Schema('person', FilmworkModel, Extractor.PERSON_MODIFIED_KEY, data, 'movies'))

            data = self.get_key_value(Extractor.GENRE_MODIFIED_KEY)
            objects.append(Schema('genre', FilmworkModel, Extractor.GENRE_MODIFIED_KEY, data, 'movies'))

            data = self.get_key_value(Extractor.FILM_MODIFIED_KEY)
            objects.append(Schema('film_work', FilmworkModel, Extractor.FILM_MODIFIED_KEY, data, 'movies'))

            data = self.get_key_value(Extractor.PERSON_IN_FILMS_MODIFIED_KEY)
            objects.append(Schema('person', PersonModel, Extractor.PERSON_IN_FILMS_MODIFIED_KEY, data, 'persons'))

            data = self.get_key_value(Extractor.GENRE_IN_FILMS_MODIFIED_KEY)
            objects.append(Schema('genre', GenreModel, Extractor.GENRE_IN_FILMS_MODIFIED_KEY, data, 'genres'))

            # перебираем последовательно 'person', 'genre', 'film_work' для записи в индекс movies
            # а также далее 'person' и 'genre' для записи в индексы persons и genres соответственно
            for cur_model in objects:
                # Считывание данных из PG
                with self.conn.cursor() as cur:

                    # запрашиваем CHUNK которые изменились после даты _MODIFIED
                    cur = self.query_exec(cur, self.get_query(cur_model))

                    while records := cur.fetchmany(self.fetch_size):
                        # формируем (кусочек) UUIN сущностей
                        changed_entities = [record for record in records]
                        # запомним дату последнего из fetch_size для изменения статуса
                        cur_model.modified, changed_entities = self.get_date_from_chunk_and_cut(changed_entities)

                        if changed_entities:
                            # Готовим данные связанные с изменениями и отправляем в ES в соответствующий индекс
                            if cur_model.es_index == 'movies':
                                self.get_films_and_send_to_es(cur_model, changed_entities)
                            else:
                                self.get_data_and_send_to_es(cur_model, changed_entities)

            Extractor.cnt_part_load = 0
            Extractor.cnt_successes = 0

    @staticmethod
    def make_names(film_work: FilmworkModel) -> FilmworkModel:
        """Уточнение данных, для соответствия
        маппингу индекса в ElasticSearch
        """
        if not film_work.director:
            film_work.director = []
        if film_work.writers:
            film_work.writers_names = [writer.full_name for writer in film_work.writers]
        if film_work.actors:
            film_work.actors_names = [actor.full_name for actor in film_work.actors]

        return film_work

    def postgres_enricher(self):
        """Метод работает со списком self.films_to_es,
        по которому дополняет данные из остальных таблиц
        и передает подготовленные данные в Тransform.
        """
        if not self.films_to_es:
            return None

        query = f"""
                SELECT row_to_json(film) as films
                FROM 
                (
                    SELECT 	
                        fw.id uuid, 
                        fw.title,
                        fw.description,
                        fw.rating as imdb_rating,
                        fw.type,
                        fw.created_at,
                        fw.updated_at,
                        (	
                            SELECT json_agg(actors_group)
                            FROM 
                            (
                                SELECT
                                    p.id uuid, 
                                    p.full_name as full_name
                                FROM content.person_film_work pfw, content.person p
                                WHERE pfw.film_work_id = fw.id AND pfw.person_id = p.id AND pfw.role='actor'
                            ) actors_group
                        ) as actors,
                        ( 
                            SELECT json_agg(writers_group)
                            FROM 
                            (
                                SELECT
                                    p.id uuid, 
                                    p.full_name as full_name
                                FROM 
                                    content.person_film_work pfw, 
                                    content.person p
                                WHERE 
                                    pfw.film_work_id = fw.id
                                AND 
                                    pfw.person_id = p.id 
                                AND 
                                    pfw.role='writer'
                            ) writers_group
                        ) as writers,	
                        (	
                            SELECT 
                                json_agg(p.full_name)                            
                            FROM 
                                content.person_film_work pfw, 
                                content.person p
                            WHERE
                                pfw.film_work_id = fw.id 
                            AND 
                                pfw.person_id = p.id 
                            AND 
                                pfw.role='director'
                        ) as director,                   
                        (
                            SELECT json_agg(g.name)
                            FROM
                                content.genre_film_work gfw, 
                                content.genre g
                            WHERE 
                                gfw.film_work_id = fw.id 
                            AND 
                                gfw.genre_id = g.id
                        ) as genre
                FROM content.film_work as fw
                WHERE fw.id IN ({', '.join(f"'{el}'" for el in self.films_to_es)})
                ) film;
                """

        # Считывание данных из PG и обогащение
        with self.conn.cursor() as cur:
            cur = self.query_exec(cur, query)

            while records := cur.fetchmany(self.fetch_size):
                raw_records = [FilmworkModel(**record['films']) for record in records]
                film_works_to_elastic = [self.make_names(record) for record in raw_records]
                self.push_to_es(film_works_to_elastic, es_index='movies')

    def push_to_es(self, data_to_elastic: list, es_index: str):
        t = Transform()
        cnt = len(data_to_elastic)

        Extractor.cnt_load += cnt
        Extractor.cnt_part_load = cnt
        Extractor.cnt_successes = t.prepare_and_push(data_to_elastic,
                                                     es_index=es_index,
                                                     chunk_size=cnt,
                                                     host_name=self.es_host,
                                                     port=self.es_port)
