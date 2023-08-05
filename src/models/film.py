# -*- coding: utf-8 -*-
"""Модуль, где определена модель кинопроизведения."""
from typing import List, Optional
from uuid import UUID

from src.models.base_model_improved import BaseModelImproved


class Participant(BaseModelImproved):
    """Модель данных персоны, участвующей в создании фильма."""

    id: UUID
    name: str


class FilmGenre(BaseModelImproved):  # TODO стоит ли наследовать модели от общего класса?
    """Модель данных жанра, к которому относится фильм."""

    id: UUID
    name: str


class Film(BaseModelImproved):
    """Модель данных кинопроизведения (минимальная - для главной страницы)."""

    id: UUID
    title: str
    imdb_rating: float


class FilmDetailed(Film):
    """Схема данных подробностей о кинопроизведении."""

    genre: Optional[List[FilmGenre]]  # TODO: уточнить, т.к.
    # в прошлом спринте у меня здесь был просто str
    description: Optional[str]
    director: Optional[List[str]]
    actors_names: Optional[List[str]]
    writers_names: Optional[List[str]]
    actors: Optional[List[Participant]]
    writers: Optional[List[Participant]]
