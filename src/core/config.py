# -*- coding: utf-8 -*-
import logging
import os
from logging import config as logging_config

from pydantic import Field, Extra, ValidationError
from pydantic_settings import BaseSettings

from src.core.logger import LOGGING


class Settings(BaseSettings):
    # Название проекта. Используется в Swagger-документации
    PROJECT_NAME: str = Field(env='PROJECT_NAME')
    # Настройки Redis
    REDIS_HOST: str = Field(env='REDIS_HOST')
    REDIS_PORT: int = Field(env='REDIS_PORT')
    # Настройки Elasticsearch
    ES_HOST: str = Field(env='ES_HOST')
    ES_PORT: int = Field(env='ES_PORT')
    # Время жизни кэша Redis
    CACHE_TIME_LIFE: int = Field(env='CACHE_TIME_LIFE')

    class Config:
        env_file = '.env'
        extra = Extra.ignore


settings = Settings()
print(settings.model_dump())


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

""" TODO: удалить блок при успешной работе класса конфигурации

# Название проекта. Используется в Swagger-документации
PROJECT_NAME = os.getenv('PROJECT_NAME', 'movies')

# Настройки Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Настройки Elasticsearch
ELASTIC_HOST = os.getenv('ELASTIC_HOST', 'es')
ELASTIC_PORT = int(os.getenv('ELASTIC_PORT', 9200))
"""

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
