from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, Literal
from dataclasses import dataclass, field


@dataclass
class Schema:
    table: str
    key: str
    modified: str
    es_index: Literal['movies', 'persons']


class PersonMixin(BaseModel):
    uuid: UUID
    full_name: str


class FilmworkModel(BaseModel):
    uuid: UUID
    title: str
    description: str | None
    imdb_rating: Optional[float] = None
    type: str = Field(exclude=True)
    created_at: datetime = Field(exclude=True)
    updated_at: datetime = Field(exclude=True)
    actors: Optional[list[PersonMixin]] = None
    writers: Optional[list[PersonMixin]] = None
    director: Optional[list[str]] = []
    genre: Optional[list[str]] = None
    writers_names: Optional[list[str]] = None
    actors_names: Optional[list[str]] = None


class PortfolioFilm(BaseModel):
    uuid: UUID
    roles: list[str]


class PersonModel(PersonMixin):
    uuid: UUID
    full_name: str
    films: Optional[list[PortfolioFilm]]





