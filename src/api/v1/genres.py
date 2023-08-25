#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Модуль реализует API для доступа к информации о жанрах."""

import json
import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.services.genre import GenreService, get_genre_service

router = APIRouter()


# Модель ответа API по жанру
class Genre(BaseModel):
    uuid: UUID
    name: str


# Определяем функцию для преобразования UUID в строку
def serialize_uuid(uuid_obj: UUID) -> str:
    """Функция переводит тип UUID в str

    Используется для json.dumps
    json не умеет сериализовать тип UUID по умолчанию
    """
    if isinstance(uuid_obj, UUID):
        return str(uuid_obj)
    raise TypeError('Object of type {0} is not UUID type'.format(type(uuid_obj)))


# Регистрируем обработчик genre_details
# на обработку запросов по адресу <some_prefix>/some_id
# позже подключим роутер к корневому роутеру
# и адрес запроса будет выглядеть так — /api/v1/genres/some_id
@router.get(
    '/{genre_id}',
    response_model=Genre,
    summary='Запрос жанра по UUID.',
    description='Полная информация о жанре: UUID и наименование.',
)
async def genre_details(
    genre_id: str,
    genre_service: GenreService = Depends(get_genre_service),
) -> Genre:

    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')

    # Перекладываем данные из `models.Genre` в `Genre`
    # Модель бизнес-логики (для ответа API), как правило, отличается от общей модели данных

    obj = Genre(uuid=genre.uuid, name=genre.name)
    pretty_object = json.dumps(obj.model_dump(), default=serialize_uuid, indent=4)
    logging.debug('Объект для выдачи {0}:\n{1}'.format(obj.__class__, pretty_object))
    return obj


@router.get(
    '/',
    response_model=list[Genre],
    summary='Запрос всех жанров.',
    description='Будут выданы все существующие жанры.',
)
async def all_genres(
    genre_service: GenreService = Depends(get_genre_service),
) -> list[Genre]:

    genres = await genre_service.get_genres()
    if not genres:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='no genres in database')

    logging.debug('Объект для выдачи list[Genres]:\n{0}'.format(genres))

    # Ответ клиенту без лишних данных (без description). Трансформация из model.Genre в Genre на лету
    return genres
