# -*- coding: utf-8 -*-
from typing import Optional

from redis.asyncio import Redis

from src.core.config import REDIS_HOST, REDIS_PORT

redis: Optional[Redis] = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
)

# Функция понадобится при внедрении зависимостей
async def get_redis() -> Redis:
    return redis
