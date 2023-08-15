# -*- coding: utf-8 -*-
import logging

from typing import Optional
from redis.asyncio import Redis

redis: Optional[Redis] = None


# Функция понадобится при внедрении зависимостей
async def get_redis() -> Redis:
    return redis


def generate_cache_key(index: str, params_to_key: dict) -> str:
    """Генерирует ключ по полученным параметрам
    Ключ для кэша задается в формате индекс::параметр::значение::параметр::значение и т.д.
    Функция сортирует параметры запроса

    :param index: имя индекса ЭС
    :param params_to_key: словарь с параметрами и значениями для кэша
    :return: строка - имя кэша для Redis
    """

    if not params_to_key:
        logging.error("Невозможно сгенерировать кэш-ключ: не переданы параметры")
        raise Exception

    sorted_keys = list(sorted(params_to_key.keys()))
    cache_key = index + '::' + '::'.join([key + '::' + str(params_to_key[key]) for key in sorted_keys])

    logging.debug(f"Кэш-ключ сгенерирован: {cache_key}")
    return cache_key
