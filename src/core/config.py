"""Конфигурация backend-приложения movies."""
from logging import config as logging_config

from pydantic_settings import BaseSettings

from src.core.logger import LOGGING


class Settings(BaseSettings):
    """Класс настроек backend-приложения movies."""

    PROJECT_NAME: str  # Название проекта. Используется в Swagger-документации

    REDIS_HOST: str
    REDIS_PORT: int
    CACHE_TIME_LIFE: int  # Время жизни кэша Redis

    ES_HOST: str
    ES_PORT: int


settings = Settings()  # type: ignore

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)
