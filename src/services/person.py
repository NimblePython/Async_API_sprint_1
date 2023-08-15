# -*- coding: utf-8 -*-
import logging

from functools import lru_cache
from typing import Optional
from pydantic import TypeAdapter

from elasticsearch import AsyncElasticsearch, NotFoundError

from fastapi import Depends
from redis.asyncio import Redis

from src.db.elastic import get_elastic
from src.db.redis import get_redis, generate_cache_key
from src.models.person import Person

from src.core import config


PERSONS_SEARCH_ADAPTER = TypeAdapter(list[Person])

logger = logging.getLogger(__name__)


# PersonService содержит бизнес-логику по работе с персоналиями.
class PersonService(object):
    def __init__(
            self,
            redis: Redis,
            elastic: AsyncElasticsearch
    ):
        self.redis = redis
        self.elastic = elastic

    async def search_person(
            self,
            query: str,
            page_number: int,
            page_size: int,
    ) -> list[Person] | None:

        # параметры ключа для кэша
        params_to_key = {
            'query': query,
            'page_size': str(page_size),
            'page_number': str(page_number),
        }
        # создаём ключ для кэша
        cache_key = generate_cache_key('persons', params_to_key)

        # Пытаемся получить данные из кеша
        persons = await self._person_search_from_cache(cache_key)
        if not persons:
            # Если данных нет в кеше, то ищем его в Elasticsearch
            search_results = await self.elastic.search(
                index='persons',
                body={
                    'query': {'match': {'full_name': query}},
                    'from': (page_number - 1) * page_size,
                    'size': page_size,
                }
            )
            persons = [Person(**hit['_source']) for hit in search_results['hits']['hits']]
            if not persons:
                # Если он отсутствует в Elasticsearch, значит, персонажа такого вообще нет в базе
                return None
            # Сохраняем поиск по персонажу в кеш
            await self._put_person_search_to_cache(cache_key, persons)

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

        # параметры ключа для кэша
        params_to_key = {
            'uuid': person_id,
        }
        # создаём ключ для кэша
        cache_key = generate_cache_key('persons', params_to_key)

        # Пытаемся получить данные о персоне из кеша, используя команду get
        person_data = await self.redis.get(cache_key)
        if not person_data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        return Person.model_validate_json(person_data)  # возвращаем десериализованный объект Person

    async def _put_person_to_cache(self, person: Person):
        """Сохраняет данные о персоне, используя команду set
        """
        # параметры ключа для кэша
        params_to_key = {
            'uuid': person.uuid,
        }
        # создаём ключ для кэша
        cache_key = generate_cache_key('persons', params_to_key)

        await self.redis.set(cache_key, person.model_dump_json(), config.settings.CACHE_TIME_LIFE)

    async def _person_search_from_cache(self, cache_key: str) -> list[Person] | None:
        """
        Ищет информацию в кеше Redis

        :param cache_key: ключ кеша - `запрос:номер_страницы:число_элементов`
        :return: возвращаем десериализованный объект List[Person] или None
        """
        # Пытаемся получить данные о персоне из кеша, используя команду get
        serialized_search_person_data = await self.redis.get(cache_key)
        if not serialized_search_person_data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        return PERSONS_SEARCH_ADAPTER.validate_json(serialized_search_person_data)

    async def _put_person_search_to_cache(self, cache_key: str, persons: list[Person]):
        """Сохраняет результат поиска, используя команду set
        """

        await self.redis.set(
            cache_key,
            PERSONS_SEARCH_ADAPTER.dump_json(persons),
            config.settings.CACHE_TIME_LIFE,
        )


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
