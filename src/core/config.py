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

    # Далее я закомментировал аналог того, что делает .env dotenv.
    # Нам это не нужно, т.к. предполагаем, что у нас все переменные уже загружены в окружение:
    # при локальном запуске - средствами IDE (.env.local),
    # при запуске в docker-compose - средствами docker-compose (.env)

    # в pycharm'е могут быть проблемы с загрузкой .env.local в переменные окружения:
    # из коробки pycharm в режиме debug не позволяет этого делать, позволяет лишь задавать перемен-
    # ные поштучно. Существует плагин с названием типа "envfile".

    # Если запуск в режиме debug в pycharm (обозначенным выше способом) останется проблемой,
    # можем вернуться к рассмотрению конструкции ниже и решить, как динамически задавать
    # env_file

    # > class Config:
    # >    env_file = '.env'
    # >    extra = Extra.ignore


settings = Settings()  # type: ignore

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)
