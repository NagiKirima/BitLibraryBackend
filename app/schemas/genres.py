from pydantic import BaseModel


class GenreCreate(BaseModel):
    genre_name: str

class GenreUpdate(BaseModel):
    genre_name: str
