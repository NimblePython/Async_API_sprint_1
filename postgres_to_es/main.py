"""ETL. Модуль main.

Приложение по регулярному просеиванию данных в БД PostgreSQL для
выявления измененных, с целью обновления этих данных в БД в ElasticSearch (ES)
ES содержит эту же информацию для обеспечения (предоставления) функции полнотекстового поиска.
"""

import configparser
import logging
import os
from contextlib import closing

import extractor
import psycopg2
from backoff_dec import backoff
from dotenv import find_dotenv, load_dotenv
from psycopg2.extras import DictCursor

load_dotenv(find_dotenv())

#  При запуске считать состояние.
#  Генерировать номер подключения сохранить состояние.
#  Подключиться к БД
#  Атомарно выполнить:
#  1. Скачать пачку данных
#  2. Трансформировать данные
#  3. Передать ElasticSearch на включение в индекс
#  4. Пометить выполненное состояние
#  В случае сбоя выполнения пп 1-4 повторно выполнить эти действия.
#  Перейти к следующей пачке данных, пока есть данные


@backoff()
def query_exec(cursor, query_to_exec):
    """Отправляет SQL запрос в PostgreSQL.

    Args:
        cursor: Курсор в БД PostgreSQL
        query_to_exec: Запрос SQL

    Returns:
        Возвращает курсор с результатом запроса
    """
    cursor.execute(query_to_exec)
    return cursor


@backoff()
def connect_to_db(dsl):
    """Соединение с PostgreSQL.

    Args:
        dsl: Параметры подключения к СУБД PostgreSQL

    Returns:
        Возвращает соединение с БД PostgreSQL
    """
    return psycopg2.connect(**dsl, cursor_factory=DictCursor)


if __name__ == '__main__':
    config = configparser.ConfigParser()  # создаём объект парсера конфига
    config.read('settings.ini')
    log_level = config['Log']['log_level']
    level = {
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'WARNING': logging.WARNING,
    }

    logging.basicConfig(
        level=level[log_level],
        format='%(asctime)s %(levelname)s %(message)s',
    )

    pg_db = os.environ.get('POSTGRES_DB')
    usr = os.environ.get('POSTGRES_USER')
    pwd = os.environ.get('POSTGRES_PASSWORD')
    pg_host = os.environ.get('POSTGRES_HOST')
    pg_port = int(os.environ.get('POSTGRES_PORT'))
    es_host = os.environ.get('ES_HOST')
    es_port = int(os.environ.get('ES_PORT'))

    pg_dsl = {'dbname': pg_db, 'user': usr, 'password': pwd, 'host': pg_host, 'port': pg_port}
    es_dsl = {'host': es_host, 'port': es_port}

    try:
        with closing(connect_to_db(pg_dsl)) as connection:
            extract = extractor.Extractor(connection, es_dsl)
            extract.postgres_producer()

    except Exception as err:
        logging.exception('%s: %s' % (err.__class__.__name__, err))
