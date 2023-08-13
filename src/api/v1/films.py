#!/usr/bin/python
# -*- coding: utf-8 -*-
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from uuid import UUID
from src.services.film import FilmService, get_film_service

# Объект router, в котором регистрируем обработчики
router = APIRouter()

# FastAPI в качестве моделей использует библиотеку pydantic
# https://pydantic-docs.helpmanual.io
# У неё есть встроенные механизмы валидации, сериализации и десериализации
# Также она основана на дата-классах


# Модель ответа API
class Film(BaseModel):
    uuid: UUID
    title: str


# С помощью декоратора регистрируем обработчик film_details
# На обработку запросов по адресу <some_prefix>/some_id
# Позже подключим роутер к корневому роутеру 
# И адрес запроса будет выглядеть так — /api/v1/films/some_id
# В сигнатуре функции указываем тип данных, получаемый из адреса запроса (film_id: str) 
# И указываем тип возвращаемого объекта — Film

# Внедряем FilmService с помощью Depends(get_film_service)
@router.get('/{film_id}', response_model=Film)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_by_id(film_id)
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
    return Film(id=film.id, title=film.title)

# Запросы, которые нужно уметь обрабатывать:

# 1. Главная страница. На ней выводятся популярные фильмы. Пока у вас есть только один признак,
# который можно использовать в качестве критерия популярности - imdb_rating

#   GET /api/v1/films?sort=-imdb_rating&page_size=50&page_number=1
#   [
#   {
#     "uuid": "uuid",
#     "title": "str",
#     "imdb_rating": "float"
#   },
#   ...
#   ]


@router.get("/api/v1/films")
async def get_popular_films(
    sort: str = Query("-imdb_rating", description="Sort by field"),
    page_size: int = Query(50, description="Number of items per page", ge=1),
    page_number: int = Query(1, description="Page number", ge=1),
    film_service: FilmService = Depends(),
):
    valid_sort_fields = ("imdb_rating", "-imdb_rating",)
    if sort not in valid_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid value for 'sort' parameter")
    
    desc = sort[0] == '-'
    
    try:
        films = await film_service.get_popular_films(
            desc_order=desc,
            page_size=page_size,
            page_number=page_number,
        )
        return films
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 2. Жанр и популярные фильмы в нём. Это просто фильтрация.

# GET /api/v1/films?genre=<uuid:UUID>&sort=-imdb_rating&page_size=50&page_number=1
# [
# {
#   "uuid": "uuid",
#   "title": "str",
#   "imdb_rating": "float"
# },
# ...
# ]

# 3. Поиск по фильмам (2.1. из т.з.)
# GET /api/v1/films/search?query=star&page_number=1&page_size=50
# [
# {
#   "uuid": "uuid",
#   "title": "str",
#   "imdb_rating": "float"
# },
# ...
# ]

# 4. Полная информация по фильму (т.з. 3.1.)
#   http request
# GET /api/v1/films/<uuid:UUID>/
# {
# "uuid": "uuid",
# "title": "str",
# "imdb_rating": "float",
# "description": "str",
# "genre": [
#   { "uuid": "uuid", "name": "str" },
#   ...
# ],
# "actors": [
#   {
#     "uuid": "uuid",
#     "full_name": "str"
#   },
#   ...
# ],
# "writers": [
#   {
#     "uuid": "uuid",
#     "full_name": "str"
#   },
#   ...
# ],
# "directors": [
#   {
#     "uuid": "uuid",
#     "full_name": "str"
#   },
#   ...
# ],
# }

# 5. Похожие фильмы. Похожесть можно оценить с помощью ElasticSearch, но цель модуля не в этом.
# Сделаем просто: покажем фильмы того же жанра.
# /api/v1/films?...

# 6. Фильмы по персоне. (т.з. 4.2)
# /api/v1/persons/<uuid:UUID>/film/

# GET /api/v1/persons/<uuid:UUID>/film
# [
# {
#   "uuid": "uuid",
#   "title": "str",
#   "imdb_rating": "float"
# },
# ...
# ]
