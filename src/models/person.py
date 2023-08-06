# -*- coding: utf-8 -*-
"""Модуль, где определена модель данных персон."""
from typing import List, Optional
from uuid import UUID

from src.models.base_model_improved import BaseModelImproved


class PortfolioFilm(BaseModelImproved):
    """Модель данных фильма в портфолио персоны."""

    uuid: UUID
    roles: List[str]


class Person(BaseModelImproved):
    """Модель данных персоны."""

    uuid: UUID
    full_name: str
    films: Optional[List[PortfolioFilm]]
