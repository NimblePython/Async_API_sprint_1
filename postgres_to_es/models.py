"""Модули данных для ETL."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class PersonMixin(BaseModel):
    """Миксин модели персоналий."""

    uuid: UUID
    full_name: str


class FilmworkModel(BaseModel):
    """Модель кинопроизведения."""

    uuid: UUID
    title: str
    description: str | None
    imdb_rating: Optional[float] = None
    type: str = Field(exclude=True)
    created_at: datetime = Field(exclude=True)
    updated_at: datetime = Field(exclude=True)
    actors: Optional[list[PersonMixin]] = None
    writers: Optional[list[PersonMixin]] = None
    director: Optional[list[str]] = []
    genre: Optional[list[str]] = None
    writers_names: Optional[list[str]] = None
    actors_names: Optional[list[str]] = None


class PortfolioFilm(BaseModel):
    """Модель портфолио."""

    uuid: UUID
    roles: list[str]


class PersonModel(PersonMixin):
    """Модель персоналия."""

    uuid: UUID
    full_name: str
    films: Optional[list[PortfolioFilm]]


class GenreModel(BaseModel):
    """Модель жанра."""

    uuid: UUID
    name: str
    description: Optional[str] = None


@dataclass
class Schema:
    """Класс описания схемы. Используется для соблюдения стиля DRY."""

    table: str
    model: Union[type(FilmworkModel), type(PersonModel), type(GenreModel)]
    key: str
    modified: str
    es_index: Literal['movies', 'persons', 'genres']
