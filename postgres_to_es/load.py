import logging

from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from backoff_dec import backoff
from typing import Literal
from models import FilmworkModel
from http import HTTPStatus


class Load:
    successes = 0
    docs_count = 0

    indexes_settings = {
        "refresh_interval": "1s",
        "analysis": {
            "filter": {
                "english_stop": {
                    "type": "stop",
                    "stopwords": "_english_"
                },
                "english_stemmer": {
                    "type": "stemmer",
                    "language": "english"
                },
                "english_possessive_stemmer": {
                    "type": "stemmer",
                    "language": "possessive_english"
                },
                "russian_stop": {
                    "type": "stop",
                    "stopwords": "_russian_"
                },
                "russian_stemmer": {
                    "type": "stemmer",
                    "language": "russian"
                }
            },
            "analyzer": {
                "ru_en": {
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "english_stop",
                        "english_stemmer",
                        "english_possessive_stemmer",
                        "russian_stop",
                        "russian_stemmer"
                    ]
                }
            }
        }
    }

    index_movies_mappings = {
        "dynamic": "strict",
        "properties": {
          "id": {"type": "keyword"},
          "imdb_rating": {"type": "float"},
          "genre": {"type": "keyword"},
          "title": {"type": "text", "analyzer": "ru_en", "fields": {"raw": {"type":  "keyword"}}},
          "description": {"type": "text", "analyzer": "ru_en"},
          "director": {"type": "text", "analyzer": "ru_en"},
          "actors_names": {"type": "text", "analyzer": "ru_en"},
          "writers_names": {"type": "text", "analyzer": "ru_en"},
          "actors": {"type": "nested", "dynamic": "strict", "properties": {"id": {"type": "keyword"}, "name": {"type": "text", "analyzer": "ru_en"}}},
          "writers": {"type": "nested", "dynamic": "strict", "properties": {"id": {"type": "keyword"}, "name": {"type": "text", "analyzer": "ru_en"}}}
        }
    }

    index_persons_mappings = {
        "dynamic": "strict",
        "properties": {
            "id": {
                "type": "keyword"
            },
            "full_name": {
                "type": "text",
                "analyzer": "ru_en"
            },
            "films": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {
                        "type": "keyword",
                    },
                    "roles": {
                        "type": "text",
                        "analyzer": "ru_en"
                    }
                }
            }
        }
    }

    indexes = {
        'movies': index_movies_mappings,
        'persons': index_persons_mappings,
    }

    def __init__(self, data: list, es_index: Literal[indexes.keys()], host: str, port: int):
        self.es_socket = f'http://{host}:{port}/'
        self.es = self.connect_to_es()
        self.data = data
        self.es_index = es_index  # текущий индекс с которым будет работать вставка данных

    @backoff()
    def connect_to_es(self):
        return Elasticsearch(self.es_socket)

    @backoff()
    def create_index(self):
        mappings = Load.indexes[self.es_index]
        self.es.indices.create(index=self.es_index,
                               settings=Load.indexes_settings,
                               mappings=mappings)

    @backoff()
    def check_index(self):
        if not self.es.indices.exists(index=self.es_index):
            return False
        return True

    def get_data(self) -> dict:
        for record in self.data:
            doc = dict()
            doc['_id'] = record.id
            doc['_index'] = self.es_index
            doc['_source'] = record.model_dump_json()
            yield doc

    @backoff()
    def insert_data(self, chunk_size: int) -> int:
        """
        Функция для вставки пачки записей с данными (фильмы, жанры, персоны) в ES

        :param
            chunk_size: размер пачки данных
            index_key: индекс, куда следует производить вставку
        :return: число успешно вставленнх записей
        """
        if not self.check_index():
            self.create_index()

        successful_records = 0
        for ok, action in streaming_bulk(self.es,
                                         index=self.es_index,
                                         actions=self.get_data(),
                                         chunk_size=chunk_size):
            successful_records += ok

        logging.info(f'Записано/обновлено записей в ElasticSearch: {successful_records}')

        return successful_records
