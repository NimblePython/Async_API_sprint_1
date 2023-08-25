# -*- coding: utf-8 -*-
from typing import Optional

from elasticsearch import AsyncElasticsearch

es: Optional[AsyncElasticsearch] = None


# Функция понадобится при внедрении зависимостей
async def get_elastic() -> AsyncElasticsearch:
    """Геттер, который возвращает объект- соединение с БД Elasticsearch.

    Returns:
        Активное существующее соединение с БД Elasticsearch
    """
    return es
