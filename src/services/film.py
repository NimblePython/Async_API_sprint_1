# -*- coding: utf-8 -*-
import asyncio
import logging
from functools import lru_cache
from pprint import pformat
from typing import List, Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from pydantic import TypeAdapter
from redis.asyncio import Redis

from src.core import config
from src.db.elastic import es, get_elastic
from src.db.redis import get_redis, redis
from src.models.film import Film, FilmDetailed, FilmGenre

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
FILM_ADAPTER = TypeAdapter(List[Film])

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


# FilmService содержит бизнес-логику по работе с фильмами.
# Никакой магии тут нет. Обычный класс с обычными методами.
# Этот класс ничего не знает про DI — максимально сильный и независимый.
class FilmService(object):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    # 1.1. получение фильма по uuid
    # get_by_id возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_uuid(self, film_uuid: str) -> Optional[Film]:
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        film = await self._get_film_from_cache(film_uuid)
        if not film:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            film = await self._get_film_from_elastic(film_uuid)
            if not film:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм  в кеш
            await self._put_film_to_cache(film)

        return film


    # 2.1. получение фильма из эластика по id
    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        try:
            doc = await self.elastic.get(index='movies', id=film_id)
        except NotFoundError:
            return None
        logger.debug(pformat(doc['_source']))
        return FilmDetailed(**doc['_source'])


    # 3.1. получение фильма из кэша по uuid
    async def _get_film_from_cache(self, film_uuid: str) -> Optional[Film]:
        # Пытаемся получить данные о фильме из кеша, используя команду get
        # https://redis.io/commands/get/
        film_data = await self.redis.get(film_uuid)
        if not film_data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        return FilmDetailed.model_validate_json(film_data)  # возвращаем десериализованный объект Film

    # 4.1. сохранение фильма в кэш по id:
    async def _put_film_to_cache(self, film: Film):
        # Сохраняем данные о фильме, используя команду set
        # Выставляем время жизни кеша — 5 минут
        # https://redis.io/commands/set/
        # pydantic позволяет сериализовать модель в json
        await self.redis.set(str(film.uuid), film.model_dump_json(), FILM_CACHE_EXPIRE_IN_SECONDS)
    

class PopularFilmsService(object):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    # 1.2. получение страницы списка фильмов отсортированных по популярности 
    async def get_popular_films(
        self, desc_order: bool, page_size: int, page_number: int, genre: Optional[UUID]=None,
    ) -> List[Film]:
        
        # создаём ключ для кэша
        params_to_cache = [int(desc_order), page_size, page_number]
        if genre is not None:
            params_to_cache.append(genre)
        page_cache_key = ', '.join(
            [str(elem) for elem in params_to_cache],
        )

        # запрашиваем ключ в кэше
        films_page = await self._get_popular_films_from_cache(page_cache_key)
        if not films_page:
            logger.debug('No films in cache!')
            # если в кэше нет значения по этому ключу, делаем запрос в es
            films_page = await self._get_popular_films_from_elastic(
                desc_order=desc_order,
                page_size=page_size,
                page_number=page_number,
                genre=genre,
            )
            if not films_page:
                return None
            
            # если результат не пуст - сохраняем его в кэш по ключу
            await self._put_popular_films_to_cache(
                page_cache_key=page_cache_key,
                films=films_page,    
            )
        else:
            logger.debug('Got films from cache!')
        return films_page

    # 2.2. получение из es страницы списка фильмов отсортированных по популярности 
    async def _get_popular_films_from_elastic(
        self, desc_order: bool, page_size: int, page_number: int, genre: Optional[UUID]=None
    ):
        if desc_order:
            order_name = 'desc'
            order_mode = 'max'
        else:
            order_name = 'asc'
            order_mode = 'min'

        search_body = {
            "size": page_size,
            "from": (page_number - 1) * page_size,
            "sort" : [
                {"imdb_rating" : {"order" : order_name, "mode" : order_mode}}
            ],
        }
        if genre is not None:
            genre_search_body = {
                'query':{
                    "bool": {
                        "filter": [
                            {"term": {"uuid": genre}}
                        ]
                    }
                }
            }
            genre_response = await self.elastic.search(index="genres", body=genre_search_body)
            genres = []
            for hit in genre_response["hits"]["hits"]:
                genres.append(FilmGenre(**hit["_source"]))
            genre_names = [genre.name for genre in genres]
            logger.debug('genres: %s' % (', '.join(genre_names)))
            search_body['query'] = {
                "bool": {
                    "filter": [
                        {"terms": {"genre": genre_names}},
                    ]
                }
            }

        response = await self.elastic.search(index="movies", body=search_body)

        popular_films = []
        for hit in response["hits"]["hits"]:
            popular_films.append(Film(**hit["_source"]))

        return popular_films

    # 3.2. получение страницы списка фильмов отсортированных по популярности из кэша
    async def _get_popular_films_from_cache(self, page_cache_key: str):
        films_data = await self.redis.get(page_cache_key)
        if not films_data:
            return None

        return FILM_ADAPTER.validate_json(films_data)

    # 4.2. сохранение страницы фильмов (отсортированных по популярности) в кэш:
    async def _put_popular_films_to_cache(self, page_cache_key: str, films):
        await self.redis.set(
            page_cache_key,
            FILM_ADAPTER.dump_json(films),
            FILM_CACHE_EXPIRE_IN_SECONDS,
        )


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


@lru_cache()
def get_popular_films_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PopularFilmsService:
    return PopularFilmsService(redis, elastic)


# Блок кода ниже нужен только для отладки сервиса:
if __name__ == '__main__':
    redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    es = AsyncElasticsearch(hosts=[f'http://{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'])
    service = FilmService(redis=redis, elastic=es)
    popular_films_service = PopularFilmsService(redis=redis, elastic=es)

    loop = asyncio.get_event_loop()

    resulting_film = loop.run_until_complete(
        service.get_by_uuid(
            film_uuid='a9bbc1d8-bb8a-41d2-b61a-d8ddc9b31ede',
        )
    )

    resulting_films_desc = loop.run_until_complete(
        popular_films_service.get_popular_films(
            desc_order=True,
            page_size=10,
            page_number=1,
        )
    )

    resulting_films_asc = loop.run_until_complete(
        popular_films_service.get_popular_films(
            desc_order=False,
            page_size=10,
            page_number=1,
        )
    )

    genre_uuid='49a81ffc-1670-4dcd-bbec-e224064cf99c'
    resulting_films_of_genre_desc = loop.run_until_complete(
        popular_films_service.get_popular_films(
            genre=genre_uuid,
            desc_order=True,
            page_size=10,
            page_number=1,
        )
    )

    loop.run_until_complete(redis.close())
    loop.run_until_complete(es.close())
    loop.close()
    logger.info('Single film:')
    logger.info(pformat(resulting_film))
    logger.info('Multiple films desc:')
    logger.info(pformat(resulting_films_desc))
    logger.info('Multiple films asc:')
    logger.info(pformat(resulting_films_asc))
    logger.info('Multiple films desc(of genre):')
    logger.info(pformat(resulting_films_of_genre_desc))
