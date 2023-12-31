# -*- coding: utf-8 -*-
"""Модуль, где определена модель данных жанров."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Genre(BaseModel):
    """Модель данных жанра кинопроизведения."""

    uuid: UUID
    name: str
    description: Optional[str] = None
