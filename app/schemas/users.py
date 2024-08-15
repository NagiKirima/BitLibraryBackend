from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID


class UserCreate(BaseModel):
    full_name: str
    birth_date: Optional[date] = None
    address: Optional[str] = None
    phone_number: str


class UserUpdate(BaseModel):
    full_name: str
    birth_date: date = None
    address: str = None
    phone_number: str

class UserSuccess(BaseModel):
    status: str
    id_user: UUID