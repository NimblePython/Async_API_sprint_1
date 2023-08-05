# -*- coding: utf-8 -*-
"""Модуль, где определена модель данных жанров."""
from uuid import UUID

from src.models.base_model_improved import BaseModelImproved


class Genre(BaseModelImproved):
    """Модель данных жанра кинопроизведения."""

    uuid: UUID
    name: str
    description: str
