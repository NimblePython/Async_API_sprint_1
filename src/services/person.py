# -*- coding: utf-8 -*-
"""Сервис PersonService для доступа к данным персоналий.

Модуль обеспечивающий реализацию основного сервиса.
"""
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
from src.models.person import Person

PERSONS_SEARCH_ADAPTER = TypeAdapter(list[Person])
PERSONS_CACHE_KEY = 'persons::all'

logger = logging.getLogger(__name__)


# PersonService содержит бизнес-логику по работе с персоналиями.
class PersonService:
    """Класс сервиса работы с персонами.

    Обеспечивает доступ к информации о персонах.

    """

    def __init__(
        self,
        redis: Redis,
        elastic: AsyncElasticsearch,
    ):
        """Конструктор PersonService.

        Args:
            redis: Ссылка на объект Redis.
            elastic: Ссылка на объект Elasticsearch.
        """
        self.redis = redis
        self.elastic = elastic

    async def search_person(
        self,
        query: str,
        page_number: int,
        page_size: int,
    ) -> list[Person]:
        """Полнотекстовый поиск персоны по имени.

        Args:
            query: Запрос, содержащий искомую строку (подстроку).
            page_number: Номер страницы (пагинация).
            page_size: Количество персон на одну страницу.

        Returns:
            Список персон подходящих под поисковой запрос
        """
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
                },
            )
            persons = [Person(**hit['_source']) for hit in search_results['hits']['hits']]
            # Сохраняем поиск по персонажу в кеш (даже если поиск не дал результата)
            await self._put_person_search_to_cache(cache_key, persons)

            if not persons:
                # Если он отсутствует в Elasticsearch, значит, персонажа такого вообще нет в базе
                return []

        return persons

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        """Получить детальную информацию о персоне по его UUID.

        Args:
            person_id: Идентификатор UUID персоны

        Returns:
            Десериализованный объект Person или None
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

    async def get_persons(self) -> Optional[list[Person]]:
        """Метод получения информации о всех персоналиях.

        Returns:
             Список всех персон или None, если нет ни одной персоны
        """
        # Пытаемся получить данные из кеша
        persons = await self._all_persons_from_cache()
        if not persons:
            # Если жанров нет в кеше, то ищем его в Elasticsearch
            persons = await self._all_persons_from_elastic()
            if not persons:
                return None
            await self._put_all_persons_to_cache(persons)

        return persons

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        try:
            doc = await self.elastic.get(index='persons', id=person_id)
        except NotFoundError:
            return None
        return Person(**doc['_source'])

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        """Получить информацию о персоне из кэша Redis.

        Args:
            person_id: Идентификатор UUID персоны.

        Returns:
            Десериализованный объект Person или None.
        """
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

        logging.info('Взято из кэша по ключу: {0}'.format(cache_key))
        # pydantic предоставляет удобное API для создания объекта моделей из json
        return Person.model_validate_json(person_data)

    async def _put_person_to_cache(self, person: Person):
        """
        Сохраняет данные о персоне, используя команду set.

        Args:
            person: Объект Person
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
        Ищет информацию в кеше Redis.

        Args:
            cache_key: Ключ кеша Redis

        Returns:
            Возвращаем десериализованный объект List[Person] или None
        """
        # Пытаемся получить данные о персоне из кеша, используя команду get
        serialized_search_person_data = await self.redis.get(cache_key)
        if not serialized_search_person_data:
            return None

        logging.info('Взято из кэша по ключу: {0}'.format(cache_key))
        # pydantic предоставляет удобное API для создания объекта моделей из json
        return PERSONS_SEARCH_ADAPTER.validate_json(serialized_search_person_data)

    async def _put_person_search_to_cache(self, cache_key: str, persons: list[Person]):
        """Сохраняет результат поиска, используя команду set.

        Args:
            cache_key: Ключ-кэш для записи в Redis.
            persons: Список персон для записи в Redis.
        """
        await self.redis.set(
            cache_key,
            PERSONS_SEARCH_ADAPTER.dump_json(persons),
            config.settings.CACHE_TIME_LIFE,
        )

    async def _all_persons_from_cache(self) -> Optional[list[Person]]:
        """Получает данные о всех жанрах из кеша Redis.

        Returns:
            Список жанров или None
        """
        serialized_genres_data = await self.redis.get(PERSONS_CACHE_KEY)
        if not serialized_genres_data:
            return None

        logging.info('Взято из кэша по ключу: {0}'.format(PERSONS_CACHE_KEY))
        return PERSONS_SEARCH_ADAPTER.validate_json(serialized_genres_data)

    async def _all_persons_from_elastic(self) -> Optional[list[Person]]:
        """Получает данные о персонах из ElasticSearch.

        Returns:
            Список персон или None.
        """
        query = {
            'query': {
                'match_all': {},
            },
            'from': 0,
            'size': 10000,
        }

        try:
            response = await self.elastic.search(index='persons', body=query)
        except NotFoundError:
            return None

        hits = response.get('hits', {}).get('hits', [])
        persons = [Person(**hit['_source']) for hit in hits]

        logging.debug(persons)

        return persons

    async def _put_all_persons_to_cache(self, persons: list[Person]):
        """Сохраняет данные о всех персоналиях в Redis, используя команду set.

        Args:
            persons: Список жанров для вставки в Redis
        """
        await self.redis.set(
            PERSONS_CACHE_KEY,
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
    """Провайдер для PersonService.

    Args:
        redis: DI - соединение с БД Redis.
        elastic: DI - соединение с БД ElasticSearch.

    Returns:
        PersonService: Если объект был ранее создан, то вернется он же (singleton).
    """
    return PersonService(redis, elastic)
