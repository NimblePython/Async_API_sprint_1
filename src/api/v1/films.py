#!/usr/bin/python
# -*- coding: utf-8 -*-
from http import HTTPStatus
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.models.film import Film, FilmDetailed
from src.services.film import (
    FilmService,
    MultipleFilmsService,
    get_film_service,
    get_multiple_films_service,
)

# Объект router, в котором регистрируем обработчики
router = APIRouter()

# FastAPI в качестве моделей использует библиотеку pydantic
# https://pydantic-docs.helpmanual.io
# У неё есть встроенные механизмы валидации, сериализации и десериализации
# Также она основана на дата-классах

# С помощью декоратора регистрируем обработчик film_details
# На обработку запросов по адресу <some_prefix>/some_id
# Позже подключим роутер к корневому роутеру 
# И адрес запроса будет выглядеть так — /api/v1/films/some_id
# В сигнатуре функции указываем тип данных, получаемый из адреса запроса (film_id: str) 
# И указываем тип возвращаемого объекта — Film


# 1. Главная страница. На ней выводятся популярные фильмы. Пока у вас есть только один признак,
# который можно использовать в качестве критерия популярности - imdb_rating
#   GET /api/v1/films?sort=-imdb_rating&page_size=50&page_number=1

# 2. Жанр и популярные фильмы в нём. Это просто фильтрация.
# GET /api/v1/films?genre=<uuid:UUID>&sort=-imdb_rating&page_size=50&page_number=1

# 5. Похожие фильмы. Похожесть можно оценить с помощью ElasticSearch, но цель модуля не в этом.
# Сделаем просто: покажем фильмы того же жанра.
# /api/v1/films?...

# в основном эндпойнте с использованием параметра similar

@router.get("/")
async def get_popular_films(
    similar: Optional[UUID] = Query(None, description="Get films of same genre as similar"),
    genre: Optional[UUID] = Query(None, description="Get films of given genres"),
    sort: str = Query("-imdb_rating", description="Sort by field"),
    page_size: int = Query(50, description="Number of items per page", ge=1),
    page_number: int = Query(1, description="Page number", ge=1),
    film_service: MultipleFilmsService = Depends(get_multiple_films_service),
):
    valid_sort_fields = ("imdb_rating", "-imdb_rating",)
    if sort not in valid_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid value for 'sort' parameter")
    
    desc = sort[0] == '-'
    
    try:
        films = await film_service.get_multiple_films(
            similar=similar,
            genre=genre,
            desc_order=desc,
            page_size=page_size,
            page_number=page_number,
        )
        return films
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 3. Поиск по фильмам (2.1. из т.з.)
# GET /api/v1/films/search?query=star&page_number=1&page_size=50

@router.get("/search", response_model=list[Film])
async def fulltext_search_filmworks(
    query: str = Query('Star', description="Film title or part of film title"),
    page_size: int = Query(50, description="Number of items per page", ge=1),
    page_number: int = Query(1, description="Page number", ge=1),
    pop_film_service: MultipleFilmsService = Depends(get_multiple_films_service),
) -> list[Film]:

    persons = await pop_film_service.search_films(
        query,
        page_number,
        page_size
    )

    return persons


# 4. Полная информация по фильму (т.з. 3.1.)

# Внедряем FilmService с помощью Depends(get_film_service)
@router.get('/{film_id}', response_model=FilmDetailed)
async def film_details(
    film_id: str,
    film_service: FilmService = Depends(get_film_service),
) -> FilmDetailed:
    film = await film_service.get_by_uuid(film_id)
    if not film:
        # Если фильм не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum  
                # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    # Перекладываем данные из models.Film в Film
    # Обратите внимание, что у модели бизнес-логики есть поле description 
        # Которое отсутствует в модели ответа API. 
        # Если бы использовалась общая модель для бизнес-логики и формирования ответов API
        # вы бы предоставляли клиентам данные, которые им не нужны 
        # и, возможно, данные, которые опасно возвращать
    return film
