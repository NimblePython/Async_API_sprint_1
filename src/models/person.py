# -*- coding: utf-8 -*-
"""Модуль, где определена модель данных персон."""
from typing import List, Optional
from uuid import UUID

import orjson
from pydantic import BaseModel


class PortfolioFilm(BaseModel):
    """Модель данных фильма в портфолио персоны."""

    uuid: UUID
    roles: List[str]
    # я бы добавил title, но в техническом задании этого поля нет
    # если брать аналогию с актёрами в фильмах - здесь должен быть именно title


class Person(BaseModel):
    """Модель данных персоны."""

    uuid: UUID
    full_name: str
    films: Optional[List[PortfolioFilm]]
