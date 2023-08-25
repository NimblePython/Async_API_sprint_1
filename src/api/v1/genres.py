# -*- coding: utf-8 -*-
"""Модуль реализует API для доступа к информации о жанрах."""

import json
import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.models.validation import check_uuid, serialize_uuid
from src.services.genre import GenreService, get_genre_service

router = APIRouter()


# Модель ответа API по жанру
class Genre(BaseModel):
    """Модель жанра для передачи клиенту."""

    uuid: UUID
    name: str


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
    """Детализация персоны при обращении к ручке api/v1/{person_id}.

    Args:
        genre_id: UUID персоны (актера, сценариста или режиссера).
        genre_service: DI - соединение с БД Elasticsearch и Redis.

    Returns:
        Genre - информация о жанре

    Raises:
        HTTPException: BAD_REQUEST - Если ошибка в запросе в формате UUID
        HTTPException: NOT_FOUND - Если жанр не найден
    """
    if not check_uuid(genre_id):
        # Если не формат UUID, отдаём 400 статус
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='UUID type incorrect')

    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')

    # Перекладываем данные из `models.Genre` в `Genre`
    # Модель бизнес-логики (для ответа API), как правило, отличается от общей модели данных

    genre = Genre(uuid=genre.uuid, name=genre.name)
    pretty_object = json.dumps(genre.model_dump(), default=serialize_uuid, indent=4)
    logging.debug('Объект для выдачи {0}:\n{1}'.format(genre.__class__, pretty_object))
    return genre


@router.get(
    '/',
    response_model=list[Genre],
    summary='Запрос всех жанров.',
    description='Будут выданы все существующие жанры.',
)
async def all_genres(
    genre_service: GenreService = Depends(get_genre_service),
) -> list[Genre]:
    """Функция для обработки запроса к еndpoint api/v1/genres/.

    Возвращает информацию о всех жанрах (не более 100).

    Args:
        genre_service: Связь с сервисом для доступа жанров

    Returns:
        Список жанров

    Raises:
        HTTPException: NOT_FOUND - Не найден ни один жанр
    """
    genres = await genre_service.get_genres()
    if not genres:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='no genres in database')

    logging.debug('Объект для выдачи list[Genres]:\n{0}'.format(genres))

    # Ответ клиенту без без description. Трансформация из model.Genre в Genre на лету
    return genres
