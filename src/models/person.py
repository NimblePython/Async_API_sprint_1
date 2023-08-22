# -*- coding: utf-8 -*-
"""Модуль, где определена модель данных персон."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CustomEncoder:
    @classmethod
    def encode_uuid(cls, uuid: UUID) -> str:  # TODO: этот метод добавлен по указанию ревьюера?
        # на мой взгляд избыточен и UUID в любом случае будет сериализоваться в строку.
        return str(uuid)


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

    class Config:  # TODO: эту часть нужно убрать, т.к. во втором Pydantic уже встроен достаточно
        # оптимальный json encoder.
        # А то у нас сейчас всё время ворнинг при запуске API
        # UserWarning: Valid config keys have changed in V2:
        # * 'json_encoders' has been removed
        # warnings.warn(message, UserWarning)

        json_encoders = {UUID: CustomEncoder.encode_uuid}


class PersonSearchQuery(BaseModel):
    """Модель параметров запроса при поиске персон."""

    query: str
    page_number: int = 1
    page_size: int = 50
