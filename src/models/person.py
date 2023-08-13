# -*- coding: utf-8 -*-
"""Модуль, где определена модель данных персон."""
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class PortfolioFilm(BaseModel):
    """Модель данных фильма в портфолио персоны."""

    uuid: UUID
    roles: List[str]


class Person(BaseModel):
    """Модель данных персоны."""

    uuid: UUID
    full_name: str
    films: Optional[List[PortfolioFilm]]


class PersonSearchQuery(BaseModel):
    """Модель параметров запроса при поиске персон."""
    query: str
    page_number: int = 1
    page_size: int = 50
