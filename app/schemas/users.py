from pydantic import BaseModel, Field, constr
from typing import Optional
from datetime import date
from uuid import UUID


class UserCreate(BaseModel):
    full_name: str
    birth_date: date
    address: str
    phone_number: constr(pattern=r'^7[0-9]{10}$')


class UserUpdate(BaseModel):
    full_name: str
    birth_date: date
    address: str

class UserSuccess(BaseModel):
    status: str
    id_user: UUID