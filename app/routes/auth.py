from fastapi import APIRouter, HTTPException
from schemas import SuccessLogin
from settings import settings


auth_router = APIRouter(
    prefix='/auth',
    tags=['Authorization']
)


@auth_router.post('')
async def login(
    login: str,
    password: str,
):
    if login != settings.api_user or password != settings.api_password:
        raise HTTPException(status_code=401, detail='Incorrect login or password')
    
    return SuccessLogin(status='success', api_key=settings.api_key)