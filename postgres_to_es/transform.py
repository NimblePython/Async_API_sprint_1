"""Модуль промежуточной трансформации данных перед отправкой в Elasticsearch.

Содержит реализацию класса Transform
"""
from typing import Literal

from load import Load


class Transform:
    """Класс содержит один метод подготовки данных и их отправки в ES."""

    @staticmethod
    def prepare_and_push(
        data_to_es: list,
        es_index: Literal['movies', 'persons', 'genres'],
        host_name: str,
        port: int,
        chunk_size: int = 500,
    ) -> int:
        """Метод подготавливает данные и записывает в ES.

        Args:
            data_to_es: List of films, persons или жанров to push to ES
            es_index: Index ES в который необходимо записать данные
            host_name: ElasticSearch server HOST
            port: ElasticSearch server PORT
            chunk_size: Size of data to push per time

        Returns:
            Количество успешно сохраненных в ЭС фильмов
        """
        load_to_es = Load(data_to_es, es_index, host_name, port)
        return load_to_es.insert_data(chunk_size)
