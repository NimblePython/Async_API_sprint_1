#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import json

from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from src.models.person import PersonSearchQuery, Filmography

from src.services.person import PersonService, get_person_service
from src.services.film import FilmService, get_film_service

router = APIRouter()


# Модель ответа API по персоне
class PortfolioFilm(BaseModel):
    uuid: UUID
    roles: list[str]


class Person(BaseModel):
    uuid: UUID
    full_name: str
    films: list[PortfolioFilm]


# Определяем функцию для преобразования UUID в строку
def serialize_uuid(uuid_obj):
    if isinstance(uuid_obj, UUID):
        return str(uuid_obj)
    raise TypeError(f"Object of type {type(uuid_obj)} is not JSON serializable")


# Описываем обработчик для поиска персоны
@router.get(
    "/search",
    response_model=list[Person],
    summary='Поиск по имени персонажа',
    description='Поиск персон со схожими именами: указать имя, количество записей на странице и номер страницы',
)
async def search_persons(query_params: PersonSearchQuery = Depends(),
                         person_service: PersonService = Depends(get_person_service),
                         ) -> list[Person]:
    persons = await person_service.search_person(
        query_params.query,
        query_params.page_number,
        query_params.page_size
    )

    return persons


# С помощью декоратора регистрируем обработчик person_details
# На обработку запросов по адресу <some_prefix>/some_id
# Позже подключим роутер к корневому роутеру
# И адрес запроса будет выглядеть так — /api/v1/persons/some_id
@router.get(
    '/{person_id}',
    response_model=Person,
    summary='Запрос персонажа по UUID',
    description='Информация о персоне: UUID, ФИО и список фильмов, где принял участие: UUID фильма и исполненные роли',
)
async def person_details(person_id: str,
                         person_service: PersonService = Depends(get_person_service)
                         ) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    # Перекладываем данные из `models.Person` в `Person`
    # Модель бизнес-логики (для ответа API), как правило, отличается от общей модели данных
    # Если бы использовалась общая модель для бизнес-логики и формирования ответов API
    # клиентам будут доступны лишние или секретные данные

    obj = Person(**person.model_dump())
    pretty_object = json.dumps(obj.model_dump(), default=serialize_uuid, indent=4)
    logging.debug(f'Объект для выдачи {obj.__class__}:\n{pretty_object}')
    return obj


@router.get(
    '/{person_id}/film/',
    response_model=list[Filmography],
    summary='Запрос фильмографии персоны по UUID',
    description='Полная информация о фильмографии персоны: UUID, название киноленты и рейтинг',

)
async def person_films(person_id: str,
                       person_service: PersonService = Depends(get_person_service),
                       film_service: FilmService = Depends(get_film_service)
                       ) -> list[Filmography]:

    person = await person_service.get_by_id(person_id)
    if not person:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    filmography = []
    for film in person.films:
        film_info = await film_service.get_by_uuid(str(film.uuid))
        if not film_info:
            error_msg = f"""Ошибка целостности данных:\nВ БД отсутствует фильм {film.uuid} 
            на который идет ссылка из портфолио персоны\nUUID персоны {person_id} c именем {person.full_name}
            """
            logging.error(error_msg)
        else:
            filmography.append(
                Filmography(
                    uuid=film.uuid,
                    title=film_info.title,
                    imdb_rating=film_info.imdb_rating
                )
            )

    if not filmography:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='filmography not found')

    logging.debug(f'Объект для выдачи list[Filmography]:\n{filmography}')
    return filmography
