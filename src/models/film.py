# -*- coding: utf-8 -*-
"""Модуль, где определена модель кинопроизведения."""
from typing import Optional
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

    genre: Optional[list[str]]
    description: Optional[str]
    director: Optional[list[str]]
    actors_names: Optional[list[str]]
    writers_names: Optional[list[str]]
    actors: Optional[list[Participant]]
    writers: Optional[list[Participant]]
