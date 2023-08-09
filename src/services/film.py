# -*- coding: utf-8 -*-
import asyncio
import logging
from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError

from fastapi import Depends
from redis.asyncio import Redis

from src.core import config
from src.db.elastic import es, get_elastic
from src.db.redis import get_redis, redis
from src.models.film import Film

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


logger = logging.getLogger(__name__)


# FilmService содержит бизнес-логику по работе с фильмами.
# Никакой магии тут нет. Обычный класс с обычными методами.
# Этот класс ничего не знает про DI — максимально сильный и независимый.
class FilmService(object):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    # get_by_id возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_id(self, film_id: str) -> Optional[Film]:
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        film = await self._film_from_cache(film_id)
        if not film:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            film = await self._get_film_from_elastic(film_id)
            if not film:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм  в кеш
            await self._put_film_to_cache(film)

        return film

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        try:
            doc = await self.elastic.get(index='movies', id=film_id)
        except NotFoundError:
            return None
        return Film(**doc['_source'])

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        # Пытаемся получить данные о фильме из кеша, используя команду get
        # https://redis.io/commands/get/
        film_data = await self.redis.get(film_id)
        if not film_data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        return Film.parse_raw(film_data)  # возвращаем десериализованный объект Film

    async def _put_film_to_cache(self, film: Film):
        # Сохраняем данные о фильме, используя команду set
        # Выставляем время жизни кеша — 5 минут
        # https://redis.io/commands/set/
        # pydantic позволяет сериализовать модель в json
        await self.redis.set(str(film.id), film.json(), FILM_CACHE_EXPIRE_IN_SECONDS)


# get_film_service — это провайдер FilmService.
# С помощью Depends он сообщает, что ему необходимы Redis и Elasticsearch
# Для их получения вы ранее создали функции-провайдеры в модуле db
# Используем lru_cache-декоратор, чтобы создать объект сервиса в едином экземпляре (синглтона)
@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)


# Блок кода ниже нужен только для отладки:
if __name__ == '__main__':
    redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    es = AsyncElasticsearch(hosts=[f'{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'])

    loop = asyncio.get_event_loop()
    logger.debug(redis)
    service = get_film_service(redis=redis, elastic=es)

    resulting_film = loop.run_until_complete(
        service.get_by_id(
            film_id='ac58403b-7070-4dcc-8e53-fa2d2d2284ab'
        )
    )

    loop.run_until_complete(redis.close())
    loop.run_until_complete(es.close())
    loop.close()
    logger.info(resulting_film)
