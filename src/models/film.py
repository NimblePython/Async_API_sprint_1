# -*- coding: utf-8 -*-
"""Модуль, где определена модель кинопроизведения."""
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class Participant(BaseModel):
    """Модель данных персоны, участвующей в создании фильма."""

    uuid: UUID
    full_name: str


class FilmGenre(BaseModel):
    """Модель данных жанра, к которому относится фильм."""

    uuid: UUID
    name: str


class Film(BaseModel):
    """Модель данных кинопроизведения (минимальная - для главной страницы)."""

    uuid: UUID
    title: str
    imdb_rating: float


class FilmDetailed(Film):
    """Схема данных подробностей о кинопроизведении."""

    genre: Optional[List[str]]
    description: Optional[str]
    director: Optional[List[str]]
    actors_names: Optional[List[str]]
    writers_names: Optional[List[str]]
    actors: Optional[List[Participant]]
    writers: Optional[List[Participant]]
