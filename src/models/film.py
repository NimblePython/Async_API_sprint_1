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
    """Модель данных персоны, участвующей в создании фильма."""

    id: UUID
    name: str


class FilmGenre(BaseModel):  # TODO стоит ли наследовать модели от общего класса?
    """Модель данных жанра, к которому относится фильм."""

    id: UUID
    name: str


class Film(BaseModel):
    """Модель данных кинопроизведения (минимальная - для главной страницы)."""

    id: UUID
    title: str
    imdb_rating: float

    class Config(object):
        """Класс конфигурации модели Pydantic."""

        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class FilmDetailed(BaseModel):
    """Схема данных подробностей о кинопроизведении."""

    genre: Optional[List[FilmGenre]]  # TODO: уточнить, т.к.
    # в прошлом спринте у меня здесь был просто str
    description: Optional[str]
    director: Optional[List[str]]
    actors_names: Optional[List[str]]
    writers_names: Optional[List[str]]
    actors: Optional[List[Participant]]
    writers: Optional[List[Participant]]
