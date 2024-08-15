from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional


class BookCreate(BaseModel):
    title: str
    author_ids: List[UUID]
    genre_ids: List[UUID]


class BookUpdate(BaseModel):
    title: str
    author_ids: List[UUID]
    genre_ids: List[UUID]