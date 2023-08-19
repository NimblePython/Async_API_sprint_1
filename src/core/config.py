
from logging import config as logging_config

from pydantic import Extra, Field
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
        extra = Extra.ignore


settings = Settings()

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)
