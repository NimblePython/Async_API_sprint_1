# -*- coding: utf-8 -*-
"""Модуль, где определена модель данных жанров."""
from uuid import UUID

from pydantic import BaseModel


class Genre(BaseModel):
    """Модель данных жанра кинопроизведения."""

    id: UUID  # TODO: в т.з. это поле названо uuid
    name: str
    description: str
