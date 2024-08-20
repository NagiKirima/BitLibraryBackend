from pydantic import BaseModel


class AuthorCreate(BaseModel):
    author_name: str

class AuthorEdit(BaseModel):
    author_name: str
