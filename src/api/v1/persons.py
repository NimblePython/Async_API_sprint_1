#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Модуль реализует API для доступа к информации о персоналиях."""
import json
import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.models.person import Filmography, PersonSearchQuery
from src.services.film import FilmService, get_film_service
from src.services.person import PersonService, get_person_service

router = APIRouter()


# Модель ответа API по персоне
class PortfolioFilm(BaseModel):
    """Модель данных - информация о фильме,
    где принимала участие персона, и ее ролях

    Свойства:
        UUID фильма
        Список ролей персоны в этом фильме.
    """
    uuid: UUID
    roles: list[str]


class Person(BaseModel):
    """Модель данных - Персона,

    Свойства:
        UUID персоны.
        Полное имя (ФИО) в одной строке.
        Список с Портфолио (фильм и роли в нём).
    """
    uuid: UUID
    full_name: str
    films: list[PortfolioFilm]


# Определяем функцию для преобразования UUID в строку
def serialize_uuid(uuid_obj):
    if isinstance(uuid_obj, UUID):
        return str(uuid_obj)
    raise TypeError('Object of type {0} is not JSON serializable'.format(type(uuid_obj)))


# Описываем обработчик для поиска персоны
@router.get(
    '/search',
    response_model=list[Person],
    summary='Поиск по имени персонажа',
    description='Поиск персон со схожими именами: указать имя, количество записей на странице и номер страницы',
)
async def search_persons(
    query_params: PersonSearchQuery = Depends(),
    person_service: PersonService = Depends(get_person_service),
) -> list[Person] | None:
    """Полнотекстовый поиск персон по части имени

    Args:
        query_params: Параметры запроса
        person_service: Соединение с БД

    Returns:
        Список персон удовлетворяющих поисковому запросу.
    """
    return await person_service.search_person(
        query_params.query,
        query_params.page_number,
        query_params.page_size,
    )


# С помощью декоратора регистрируем обработчик person_details
# На обработку запросов по адресу <some_prefix>/some_id
# Позже подключим роутер к корневому роутеру
# И адрес запроса будет выглядеть так — /api/v1/persons/some_id
@router.get(
    '/{person_id}',
    response_model=Person,
    summary='Запрос персонажа по UUID.',
    description='Информация о персоне: UUID, ФИО и список фильмов с сыгранными ролями.',
)
async def person_details(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
) -> Person:
    """Детализация персоны при обращении к ручке api/v1/{person_id}.

    Args:
        person_id: UUID персоны (актера, сценариста или режиссера).
        person_service: DI - соединение с БД Elasticsearch и Redis.

    Returns:
        Person - информация о персоне
    """
    person = await person_service.get_by_id(person_id)
    if not person:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    # Перекладываем данные из `models.Person` в `Person`
    # Модель бизнес-логики (для ответа API), как правило, отличается от общей модели данных
    # Если бы использовалась общая модель для бизнес-логики и формирования ответов API
    # клиентам будут доступны лишние или секретные данные

    person = Person(**person.model_dump())
    pretty_object = json.dumps(person.model_dump(), default=serialize_uuid, indent=4)
    logging.debug('Объект для выдачи {0}:\n{1}'.format(person.__class__, pretty_object))
    return person


@router.get(
    '/{person_id}/film/',
    response_model=list[Filmography],
    summary='Запрос фильмографии персоны по UUID.',
    description='Полная информация о фильмографии персоны: UUID, название киноленты и рейтинг.',
)
async def person_films(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
    film_service: FilmService = Depends(get_film_service),
) -> list[Filmography]:

    person = await person_service.get_by_id(person_id)
    if not person:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    filmography = []
    for film in person.films:
        film_info = await film_service.get_by_uuid(str(film.uuid))
        if film_info:
            filmography.append(
                Filmography(
                    uuid=film.uuid,
                    title=film_info.title,
                    imdb_rating=film_info.imdb_rating,
                ),
            )
        else:
            error_msg = """Ошибка целостности данных:\n
            В БД отсутствует фильм {0} на который идет ссылка из портфолио персоны\n
            UUID персоны {1} c именем {2}""".format(film.uuid, person_id, person.full_name)
            logging.error(error_msg)

    if not filmography:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='filmography not found')

    logging.debug('Объект для выдачи list[Filmography]:\n{0}'.format(filmography))
    return filmography
