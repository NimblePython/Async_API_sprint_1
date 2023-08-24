"""Модуль работы с Elasticsearch.

Описание класса Load, который реализует необходимые методы для записи данных.
"""
import logging
from typing import Literal

from backoff_dec import backoff
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk


class Load:
    """Класс взаимодействия с БД Elasticsearch.

    Соединение с БД. Проверка индексов. Создание индексов при необходимости.
    Сохранение данных в ES. Мониторинг успешных записей.
    """

    successes = 0
    docs_count = 0

    indexes_settings = {
        'refresh_interval': '1s',
        'analysis': {
            'filter': {
                'english_stop': {
                    'type': 'stop',
                    'stopwords': '_english_',
                },
                'english_stemmer': {
                    'type': 'stemmer',
                    'language': 'english',
                },
                'english_possessive_stemmer': {
                    'type': 'stemmer',
                    'language': 'possessive_english',
                },
                'russian_stop': {
                    'type': 'stop',
                    'stopwords': '_russian_',
                },
                'russian_stemmer': {
                    'type': 'stemmer',
                    'language': 'russian',
                },
            },
            'analyzer': {
                'ru_en': {
                    'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'english_stop',
                        'english_stemmer',
                        'english_possessive_stemmer',
                        'russian_stop',
                        'russian_stemmer',
                    ],
                },
            },
        },
    }

    index_movies_mappings = {
        'dynamic': 'strict',
        'properties': {
            'uuid': {
                'type': 'keyword',
            },
            'imdb_rating': {
                'type': 'float',
            },
            'genre': {
                'type': 'keyword',
            },
            'title': {
                'type': 'text',
                'analyzer': 'ru_en',
                'fields': {
                    'raw': {
                        'type': 'keyword',
                    },
                },
            },
            'description': {
                'type': 'text',
                'analyzer': 'ru_en',
            },
            'director': {
                'type': 'text',
                'analyzer': 'ru_en',
            },
            'actors_names': {
                'type': 'text',
                'analyzer': 'ru_en',
            },
            'writers_names': {
                'type': 'text',
                'analyzer': 'ru_en',
            },
            'actors': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'uuid': {
                        'type': 'keyword',
                    },
                    'full_name': {
                        'type': 'text',
                        'analyzer': 'ru_en',
                    },
                },
            },
            'writers': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'uuid': {
                        'type': 'keyword',
                    },
                    'full_name': {
                        'type': 'text',
                        ' analyzer': 'ru_en',
                    },
                },
            },
        },
    }

    index_persons_mappings = {
        'dynamic': 'strict',
        'properties': {
            'uuid': {
                'type': 'keyword',
            },
            'full_name': {
                'type': 'text',
                'analyzer': 'ru_en',
            },
            'films': {
                'type': 'nested',
                'dynamic': 'strict',
                'properties': {
                    'uuid': {
                        'type': 'keyword',
                    },
                    'roles': {
                        'type': 'text',
                        'analyzer': 'ru_en',
                    },
                },
            },
        },
    }

    index_genres_mappings = {
        'dynamic': 'strict',
        'properties': {
            'uuid': {
                'type': 'keyword',
            },
            'name': {
                'type': 'text',
                'analyzer': 'ru_en',
            },
            'description': {
                'type': 'text',
                'analyzer': 'ru_en',
            },
        },
    }

    indexes = {
        'movies': index_movies_mappings,
        'persons': index_persons_mappings,
        'genres': index_genres_mappings,
    }

    def __init__(
        self,
        data_to_es: list,
        es_index: Literal['movies', 'persons', 'genres'],
        host: str,
        port: int,
    ):
        """Конструктор с инициализацией соединения с ES.

        Args:
            data_to_es: Список данных, которые должны будут записаться в ES
            es_index: Наименование одного из индексов, куда должны записаться данные
            host: Имя или IP адрес хоста с ES
            port: Номер порта для связи с ES
        """
        self.es_socket = 'http://{0}:{1}/'.format(host, port)
        self.es = self.connect_to_es()
        self.data_to_es = data_to_es
        self.es_index = es_index  # текущий индекс с которым будет работать вставка данных

    @backoff()
    def connect_to_es(self):
        """Создание соединения с Elasticsearch.

        Returns:
            Возвращает объект Elasticsearch связанный с БД
        """
        return Elasticsearch(self.es_socket)

    @backoff()
    def create_index(self):
        """Создание индекса, который задан в свойстве self.es_index."""
        mappings = Load.indexes[self.es_index]
        self.es.indices.create(
            index=self.es_index,
            settings=Load.indexes_settings,
            mappings=mappings,
        )

    @backoff()
    def check_index(self):
        """Проверка на наличие индекса.

        Индекс указан в свойстве self.es_index.

        Returns:
            Наличие индекса (True/False)
        """
        return self.es.indices.exists(index=self.es_index)

    def get_data(self) -> dict:
        """Генераторная функция. Получение данных построчно для метода bulk для передачи в ES.

        Метод использует свойство self.data экземпляра объекта Load

        Yields:
            Возвращается генератор со строкой (типа словарь) подготовленной для вставки в индекс
        """
        for record in self.data_to_es:
            doc = {
                '_id': record.uuid,
                '_index': self.es_index,
                '_source': record.model_dump_json(),
            }
            #  TODO: Удалить после успешного тестирования
            #  doc['_id'] = record.uuid
            #  doc['_index'] = self.es_index
            #  doc['_source'] = record.model_dump_json()

            logging.debug('Запись данных в ElasticSearch: %s' % doc)
            yield doc

    @backoff()
    def insert_data(self, chunk_size: int) -> int:
        """Функция для вставки пачки записей с данными (фильмы, жанры, персоны) в ES.

        Args:
            chunk_size: размер пачки данных

        Returns:
            Число успешно вставленных записей
        """
        if not self.check_index():
            self.create_index()

        successful_records = 0
        for ok, _ in streaming_bulk(
            self.es,
            index=self.es_index,
            actions=self.get_data(),
            chunk_size=chunk_size,
        ):
            successful_records += ok

        logging.info('Записано/обновлено записей в ElasticSearch: %s' % successful_records)

        return successful_records
