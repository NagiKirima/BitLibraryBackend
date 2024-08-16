from pydantic import BaseModel
from uuid import UUID
from datetime import date
from typing import List, Optional


class BookCreate(BaseModel):
    title: str
    author_ids: List[UUID]
    genre_ids: List[UUID]


class BookUpdate(BaseModel):
    title: str
    author_ids: List[UUID]
    genre_ids: List[UUID]


class BookBorrow(BaseModel):
    id_user: UUID
    id_book: UUID
    borrow_date: date
    return_date: date