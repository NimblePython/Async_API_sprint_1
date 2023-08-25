# -*- coding: utf-8 -*-
"""Модуль реализует сервис для доступа к информации о жанрах."""

import logging
from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from pydantic import TypeAdapter
from redis.asyncio import Redis

from src.core import config
from src.db.elastic import get_elastic
from src.db.redis import generate_cache_key, get_redis
from src.models.genre import Genre

GENRES_SEARCH_ADAPTER = TypeAdapter(list[Genre])
GENRES_CACHE_KEY = 'genres::all'

logger = logging.getLogger(__name__)


# GenreService содержит бизнес-логику по работе с персоналиями.
class GenreService(object):
    """Класс сервиса работы с жанрами.

    Обеспечивает доступ к информации о жанрах.
    """

    def __init__(
        self,
        redis: Redis,
        elastic: AsyncElasticsearch,
    ):
        """Конструктор GenreService.

        Args:
            redis: Ссылка на объект Redis.
            elastic: Ссылка на объект Elasticsearch.
        """
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        """Возвращает Жанр по его UUID из ES.

        Args:
            genre_id: Идентификатор UUID запрашиваемого жанра

        Returns:
            Информация о жанре или None, если не найден
        """
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        genre = await self._get_genre_from_cache(genre_id)
        if not genre:
            # Если жанра нет в кеше, то ищем его в Elasticsearch
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                # Если он отсутствует в Elasticsearch, значит, жанра такого нет
                return None
            # Сохраняем жанр в кеш
            await self._put_genre_to_cache(genre)

        return genre

    async def get_genres(self) -> Optional[list[Genre]]:
        """Метод получения информации о всех жанрах.

        Returns:
             Список всех жанров или None, если нет ни одного жанра
        """
        # Пытаемся получить данные из кеша
        genres = await self._all_genres_from_cache()
        if not genres:
            # Если жанров нет в кеше, то ищем его в Elasticsearch
            genres = await self._all_genres_from_elastic()
            if not genres:
                return None
            await self._put_all_genres_to_cache(genres)

        return genres

    async def _get_genre_from_elastic(self, genre_id: str) -> Optional[Genre]:
        """Получает данные о жанре из Elasticsearch, используя команду get.

        Args:
            genre_id: Идентификатор UUID жанра

        Returns:
            Жанр или None, если жанр не найден
        """
        try:
            doc = await self.elastic.get(index='genres', id=genre_id)
        except NotFoundError:
            return None
        return Genre(**doc['_source'])

    async def _get_genre_from_cache(self, genre_id: str) -> Optional[Genre]:
        """Получает данные о жанре из кеша Redis, используя команду get.

        Args:
            genre_id: Идентификатор UUID жанра

        Returns:
            Жанр (или None, если не найден, но так быть не должно, иначе - ошибка именования кэша)
        """
        params_to_key = {
            'uuid': genre_id,
        }
        cache_key = generate_cache_key('genres', params_to_key)

        serialized_genre_data = await self.redis.get(cache_key)
        if not serialized_genre_data:
            return None

        logging.info('Взято из кэша по ключу: {0}'.format(cache_key))
        return Genre.model_validate_json(serialized_genre_data)

    async def _put_genre_to_cache(self, genre: Genre):
        """Сохраняет данные о жанре в Redis, используя команду set.

        Args:
            genre: Объект жанра
        """
        # подготовка к генерации ключа
        params_to_key = {
            'uuid': genre.uuid,
        }
        cache_key = generate_cache_key('genres', params_to_key)

        await self.redis.set(
            cache_key,
            genre.model_dump_json(),
            config.settings.CACHE_TIME_LIFE,
        )

    async def _all_genres_from_cache(self) -> Optional[list[Genre]]:
        """Получает данные о всех жанрах из кеша Redis.

        Returns:
            Список жанров или None
        """
        serialized_genres_data = await self.redis.get(GENRES_CACHE_KEY)
        if not serialized_genres_data:
            return None

        logging.info('Взято из кэша по ключу: {0}'.format(GENRES_CACHE_KEY))
        return GENRES_SEARCH_ADAPTER.validate_json(serialized_genres_data)

    async def _all_genres_from_elastic(self) -> Optional[list[Genre]]:
        """Получает данные о жанре из ElasticSearch.

        Returns:
            Список жанров или None.
        """
        query = {
            'query': {'match_all': {}},
            'from': 0,
            'size': 100,
        }

        try:
            response = await self.elastic.search(index='genres', body=query)
        except NotFoundError:
            return None

        hits = response.get('hits', {}).get('hits', [])
        genres = [Genre(**hit['_source']) for hit in hits]

        logging.debug(genres)

        return genres

    async def _put_all_genres_to_cache(self, genres: list[Genre]):
        """Сохраняет данные о всех жанрах в Redis, используя команду set.

        Args:
            genres: Список жанров для вставки в Redis
        """
        await self.redis.set(
            GENRES_CACHE_KEY,
            GENRES_SEARCH_ADAPTER.dump_json(genres),
            config.settings.CACHE_TIME_LIFE,
        )


# С помощью Depends он сообщает, что ему необходимы Redis и Elasticsearch
# Для их получения вы ранее создали функции-провайдеры в модуле db
# используем lru_cache-декоратор, чтобы создать объект сервиса в едином экземпляре (синглтона)
@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    """Провайдер для GenreService.

    Args:
        redis: DI - соединение с БД Redis.
        elastic: DI - соединение с БД ElasticSearch.

    Returns:
        GenreService: Сервис для работы с жанрами (singlton)
    """
    return GenreService(redis, elastic)
