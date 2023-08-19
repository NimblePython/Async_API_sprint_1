
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


settings = Settings()

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)
