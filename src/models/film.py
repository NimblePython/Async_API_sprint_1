# -*- coding: utf-8 -*-
"""Модуль, где определена модель кинопроизведения."""
from typing import List, Optional
from uuid import UUID

import orjson
# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from pydantic import BaseModel


def orjson_dumps(value_to_dump, *, default):
    """Конвертировать в передаваемое значение в json-строку.

    "*" - обозначает конец позиционных аргументов (PEP 3102)
    To serialize a subclass or arbitrary types, specify default as a callable
    that returns a supported type. specify default as a callable that returns a supported type.

    Parameters:
        value_to_dump: значение, которое нужно конвертировать
        default: default may be a function, lambda, or callable class instance


    Returns:
        json_str: строка в формате json
    """
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(value_to_dump, default=default).decode()


class Participant(BaseModel):
    """Схема данных персоны, участвующей в создании фильма."""

    id: UUID
    name: str


class Film(BaseModel):
    """Схема данных кинопроизведения."""

    id: UUID
    imdb_rating: float
    genre: str
    title: str
    description: Optional[str]
    director: Optional[List[str]]
    actors_names: Optional[List[str]]
    writers_names: Optional[List[str]]
    actors: Optional[List[Participant]]
    writers: Optional[List[Participant]]

    class Config(object):
        """Класс конфигурации модели Pydantic."""

        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps
