import uuid

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, Literal
from dataclasses import dataclass, field


@dataclass
class Schema:
    table: str
    key: str
    modified: str


class PersonMixin(BaseModel):
    id: uuid.UUID
    name: str


class FilmworkMixin(BaseModel):
    id: uuid.UUID
    title: str


class FilmworkModel(FilmworkMixin):
    id: uuid.UUID
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


class PersonModel(PersonMixin):
    id: uuid.UUID
    name: str
    role: Literal['director', 'actor', 'writer', None]
    films: list[FilmworkMixin]





