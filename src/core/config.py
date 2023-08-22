# -*- coding: utf-8 -*-
import os
from logging import config as logging_config

from pydantic import Extra, Field
from pydantic_settings import BaseSettings

from src.core.logger import LOGGING


class Settings(BaseSettings):
    # Название проекта. Используется в Swagger-документации
    PROJECT_NAME: str = Field('movies', env='PROJECT_NAME')
    # Настройки Redis
    REDIS_HOST: str = Field('redis', env='REDIS_HOST')
    REDIS_PORT: int = Field(6379, env='REDIS_PORT')
    # Настройки Elasticsearch
    ES_HOST: str = Field('es', env='ES_HOST')
    ES_PORT: int = Field(9200, env='ES_PORT')
    # Время жизни кэша Redis
    CACHE_TIME_LIFE: int = Field(300, env='CACHE_TIME_LIFE')

    class Config:
        env_file = '.env'
        extra = Extra.ignore


settings = Settings()


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)
