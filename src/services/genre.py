# -*- coding: utf-8 -*-
import logging
from functools import lru_cache
from typing import Optional
from pydantic import TypeAdapter

from elasticsearch import AsyncElasticsearch, NotFoundError

from fastapi import Depends
from redis.asyncio import Redis

from src.db.elastic import get_elastic
from src.db.redis import get_redis
from src.models.genre import Genre

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 300 сек (5 минут)
GENRES_SEARCH_ADAPTER = TypeAdapter(list[Genre])
GENRES_CACHE_KEY = '_all_genres'

logger = logging.getLogger(__name__)


# GenreService содержит бизнес-логику по работе с персоналиями.
class GenreService(object):
    def __init__(self,
                 redis: Redis,
                 elastic: AsyncElasticsearch
                 ):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        """Возвращает Жанр по его UUID из ES.
        Возвращаемый параметр опционален, так как Жанр может отсутствовать в БД
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
        """ Получает данные о жанре из ElasticSearch
        """
        try:
            doc = await self.elastic.get(index='genres', id=genre_id)
        except NotFoundError:
            return None
        return Genre(**doc['_source'])

    async def _get_genre_from_cache(self, genre_id: str) -> Optional[Genre]:
        """ Получает данные о жанре из кеша Redis, используя команду get
        """
        serialized_genre_data = await self.redis.get(genre_id)
        if not serialized_genre_data:
            return None

        return Genre.model_validate_json(serialized_genre_data)  # возвращаем десериализованный объект Genre

    async def _put_genre_to_cache(self, genre: Genre):
        """Сохраняет данные о жанре в Redis, используя команду set
        """
        await self.redis.set(
            str(genre.uuid),
            genre.model_dump_json(),
            GENRE_CACHE_EXPIRE_IN_SECONDS
        )

    async def _all_genres_from_cache(self) -> Optional[list[Genre]]:
        """ Получает данные о всех жанрах из кеша Redis

        :return: список жанров или None
        """
        serialized_genres_data = await self.redis.get(GENRES_CACHE_KEY)
        if not serialized_genres_data:
            return None

        return GENRES_SEARCH_ADAPTER.validate_json(serialized_genres_data)

    async def _all_genres_from_elastic(self) -> Optional[list[Genre]]:
        """ Получает данные о жанре из ElasticSearch

        :return: список жанров или None
        """
        query = {
            'query': {'match_all': {}},
            'from': 0,
            'size': 100
        }

        try:
            response = await self.elastic.search(index='genres', body=query)
        except NotFoundError:
            return None

        hits = response.get("hits", {}).get("hits", [])
        genres = [hit["_source"] for hit in hits]
        return genres

    async def _put_all_genres_to_cache(self, genres: list[Genre]):
        """Сохраняет данные о всех жанрах в Redis, используя команду set
        """
        await self.redis.set(
            GENRES_CACHE_KEY,
            GENRES_SEARCH_ADAPTER.dump_json(genres),
            GENRE_CACHE_EXPIRE_IN_SECONDS
        )


# С помощью Depends он сообщает, что ему необходимы Redis и Elasticsearch
# Для их получения вы ранее создали функции-провайдеры в модуле db
# используем lru_cache-декоратор, чтобы создать объект сервиса в едином экземпляре (синглтона)
@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    """Провайдер для GenreService"""
    return GenreService(redis, elastic)
