# -*- coding: utf-8 -*-
import logging
from contextlib import asynccontextmanager

import uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from src.api.v1 import films, genres, persons
from src.core import config
from src.db import elastic, redis

VERSION_DETAILS_TEMPLATE = """
movies backend %s;
%s.

"""

logger = logging.getLogger(__name__)
logger.info(
    VERSION_DETAILS_TEMPLATE % (
        config.settings.APP_VERSION,
        config.settings.APP_VERSION_DETAILS,
    ),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Подключаемся к базам при старте сервера
    # Подключиться можем при работающем event-loop
    # Поэтому логика подключения происходит в асинхронной функции
    redis.redis = Redis(host=config.settings.REDIS_HOST, port=config.settings.REDIS_PORT)
    elastic.es = AsyncElasticsearch(
        hosts=[
            {
                'scheme': 'http',
                'host': config.settings.ES_HOST,
                'port': config.settings.ES_PORT,
            },
        ],
    )

    yield

    # Отключаемся от баз при выключении сервера
    await redis.redis.close()
    await elastic.es.close()


app = FastAPI(
    # Конфигурируем название проекта. Оно будет отображаться в документации
    title=config.settings.PROJECT_NAME,
    # Адрес документации в красивом интерфейсе
    docs_url='/api/openapi',
    # Адрес документации в формате OpenAPI
    openapi_url='/api/openapi.json',
    # Можно сразу сделать небольшую оптимизацию сервиса
    # и заменить стандартный JSON-сереализатор на более шуструю версию, написанную на Rust
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


@app.get('/api/v1/version')
async def version():
    return {
        'app': 'movies backend',
        'version': config.settings.APP_VERSION,
        'details': config.settings.APP_VERSION_DETAILS,
    }


# Подключаем роутер к серверу, указав префиксы
# Теги указываем для удобства навигации по документации
app.include_router(films.router, prefix='/api/v1/films', tags=['films'])
app.include_router(persons.router, prefix='/api/v1/persons', tags=['persons'])
app.include_router(genres.router, prefix='/api/v1/genres', tags=['genres'])

if __name__ == '__main__':
    # Приложение может запускаться командой
    # `uvicorn main:app --host 0.0.0.0 --port 8000`
    # но чтобы не терять возможность использовать дебагер,
    # запустим uvicorn сервер через python
    uvicorn.run(
        'src.main:app',
        host='0.0.0.0',
        port=8000,
    )
