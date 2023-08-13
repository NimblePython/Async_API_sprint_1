# -*- coding: utf-8 -*-
import logging
from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError

from fastapi import Depends
from redis.asyncio import Redis

from src.db.elastic import get_elastic
from src.db.redis import get_redis
from src.models.genre import Genre

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 300 сек (5 минут)


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
        genre = await self._genre_from_cache(genre_id)
        if not genre:
            # Если жанра нет в кеше, то ищем его в Elasticsearch
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                # Если он отсутствует в Elasticsearch, значит, жанра такого нет
                return None
            # Сохраняем жанр в кеш
            await self._put_genre_to_cache(genre)

        return genre

    async def _get_genre_from_elastic(self, genre_id: str) -> Optional[Genre]:
        try:
            doc = await self.elastic.get(index='genres', id=genre_id)
        except NotFoundError:
            return None
        return Genre(**doc['_source'])

    async def _genre_from_cache(self, genre_id: str) -> Optional[Genre]:
        # Пытаемся получить данные о жанре из кеша, используя команду get
        genre_data = await self.redis.get(genre_id)
        if not genre_data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        return Genre.model_validate_json(genre_data)  # возвращаем десериализованный объект Genre

    async def _put_genre_to_cache(self, genre: Genre):
        """Сохраняет данные о персоне, используя команду set
        """
        await self.redis.set(str(genre.uuid), genre.model_dump_json(), GENRE_CACHE_EXPIRE_IN_SECONDS)


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
