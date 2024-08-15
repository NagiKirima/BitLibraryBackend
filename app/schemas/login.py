from pydantic import BaseModel


class SuccessLogin(BaseModel):
    status: str
    api_key: str