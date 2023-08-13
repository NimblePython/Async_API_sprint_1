# -*- coding: utf-8 -*-
"""Модуль, где определена модель данных жанров."""
from uuid import UUID
from pydantic import BaseModel

class Genre(BaseModel):
    """Модель данных жанра кинопроизведения."""

    uuid: UUID
    name: str
    description: str
