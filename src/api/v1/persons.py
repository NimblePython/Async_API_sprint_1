#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import json

from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from typing import List


from src.services.person import PersonService, get_person_service
from src.services.film import FilmService, get_film_service

router = APIRouter()


# Модель ответа API по персоне
class PortfolioFilm(BaseModel):
    uuid: UUID
    roles: List[str]


class Person(BaseModel):
    uuid: UUID
    full_name: str
    films: List[PortfolioFilm]


class Filmography(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float


# Определяем функцию для преобразования UUID в строку
def serialize_uuid(uuid_obj):
    if isinstance(uuid_obj, UUID):
        return str(uuid_obj)
    raise TypeError(f"Object of type {type(uuid_obj)} is not JSON serializable")


# С помощью декоратора регистрируем обработчик person_details
# На обработку запросов по адресу <some_prefix>/some_id
# Позже подключим роутер к корневому роутеру
# И адрес запроса будет выглядеть так — /api/v1/persons/some_id
# В сигнатуре функции указываем тип данных, получаемый из адреса запроса (person_id: str)
# И указываем тип возвращаемого объекта — Person

# Внедряем PersonService с помощью Depends(get_person_service)
@router.get('/{person_id}', response_model=Person)
async def person_details(person_id: str,
                         person_service: PersonService = Depends(get_person_service)
                         ) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    # Перекладываем данные из models.Person в Person
    # Модель бизнес-логики (для ответа API), как правило, отличается от общей модели данных
    # Если бы использовалась общая модель для бизнес-логики и формирования ответов API
    # клиентам будут доступны данные, которые им не нужны
    # и, возможно, секретные данные, которые нельзя возвращать
    # return Person(uuid=person.uuid, full_name=person.full_name)
    obj = Person(**person.model_dump())
    pretty_object = json.dumps(obj.model_dump(), default=serialize_uuid, indent=4)
    logging.debug(f'Объект для выдачи {obj.__class__}:\n{pretty_object}')
    return obj


# TODO: так как снова создание объекта FilmService нужно уточнить что происходит с новым экземпляром и кешем
@router.get('/{person_id}/film/', response_model=List[Filmography])
async def person_films(person_id: str,
                       person_service: PersonService = Depends(get_person_service),
                       film_service: FilmService = Depends(get_film_service)
                       ) -> List[Filmography]:
    person = await person_service.get_by_id(person_id)
    if not person:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    # Перекладываем данные из models.Person в Filmography
    filmography = []
    for film in person.films:
        film_info = await film_service.get_by_id(str(film.uuid))
        filmography.append(
            Filmography(
                uuid=film.uuid,
                title=film_info.title,
                imdb_rating=film_info.imdb_rating
            )
        )

    logging.debug(f'Объект для выдачи list[Filmography]:\n{filmography}')
    return filmography
