# -*- coding: utf-8 -*-
"""Модуль, где определена модель данных персон."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Filmography(BaseModel):
    """Модель фильмографии персоны."""

    uuid: UUID
    title: str
    imdb_rating: float


class PortfolioFilm(BaseModel):
    """Модель данных фильма в портфолио персоны."""

    uuid: UUID
    roles: list[str]


class Person(BaseModel):
    """Модель данных персоны."""

    uuid: UUID
    full_name: str
    films: Optional[list[PortfolioFilm]]


class PersonSearchQuery(BaseModel):
    """Модель параметров запроса при поиске персон."""

    query: str
    page_number: int = 1
    page_size: int = 50
