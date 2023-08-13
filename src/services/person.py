# -*- coding: utf-8 -*-
import asyncio
import logging
from functools import lru_cache
from typing import Optional, List

from elasticsearch import AsyncElasticsearch, NotFoundError

from fastapi import Depends
from redis.asyncio import Redis

from src.core import config
from src.db.elastic import get_elastic
from src.db.redis import get_redis
from src.models.person import Person

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 300 сек (5 минут)


logger = logging.getLogger(__name__)


# PersonService содержит бизнес-логику по работе с персоналиями.
class PersonService(object):
    def __init__(self,
                 redis: Redis,
                 elastic: AsyncElasticsearch
                 ):
        self.redis = redis
        self.elastic = elastic

    async def search_person(self,
                            query: str,
                            page_number: int,
                            page_size: int) -> List[Person]:
        search_results = await self.elastic.search(
            index="persons",
            body={
                "query": {"match": {"full_name": query}},
                "from": (page_number - 1) * page_size,
                "size": page_size
            }
        )
        persons = [Person(**hit['_source']) for hit in search_results['hits']['hits']]
        return persons

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        """Возвращает Персонаж по его UUID из ES.
        Возвращаемый параметр опционален, так как Персонаж может отсутствовать в БД
        """

        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        person = await self._person_from_cache(person_id)
        if not person:
            # Если персоны нет в кеше, то ищем его в Elasticsearch
            person = await self._get_person_from_elastic(person_id)
            if not person:
                # Если он отсутствует в Elasticsearch, значит, персонажа такого вообще нет в базе
                return None
            # Сохраняем персонажа в кеш
            await self._put_person_to_cache(person)

        return person

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        try:
            doc = await self.elastic.get(index='persons', id=person_id)
        except NotFoundError:
            return None
        return Person(**doc['_source'])

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        # Пытаемся получить данные о персоне из кеша, используя команду get
        # https://redis.io/commands/get/
        person_data = await self.redis.get(person_id)
        if not person_data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        return Person.model_validate_json(person_data)  # возвращаем десериализованный объект Person

    async def _put_person_to_cache(self, person: Person):
        """Сохраняет данные о персоне, используя команду set
        """
        await self.redis.set(str(person.uuid), person.model_dump_json(), PERSON_CACHE_EXPIRE_IN_SECONDS)


# С помощью Depends он сообщает, что ему необходимы Redis и Elasticsearch
# Для их получения вы ранее создали функции-провайдеры в модуле db
# используем lru_cache-декоратор, чтобы создать объект сервиса в едином экземпляре (синглтона)
@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    """Провайдер для PersonService"""
    return PersonService(redis, elastic)


# Блок кода ниже нужен только для отладки сервиса:
if __name__ == '__main__':
    redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    es = AsyncElasticsearch(
        hosts=[{
            'host': config.ELASTIC_HOST,
            'port': config.ELASTIC_PORT,
            'scheme': 'http'
        }]
    )
    service = PersonService(redis=redis, elastic=es)

    loop = asyncio.get_event_loop()

    resulting_person = loop.run_until_complete(
        service.get_by_id(
            person_id='017713b9-24cf-43a6-ab62-6b5e476499b8',
        )
    )

    loop.run_until_complete(redis.close())
    loop.run_until_complete(es.close())
    loop.close()
    logger.info(resulting_person)
