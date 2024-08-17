from fastapi import APIRouter, HTTPException, Body
from schemas import SuccessLogin
from settings import settings


auth_router = APIRouter(
    prefix='/login',
    tags=['Authorization']
)


@auth_router.post('')
async def login(
    login: str = Body(),
    password: str = Body(),
):
    if login != settings.api_user or password != settings.api_password:
        raise HTTPException(status_code=401, detail='Incorrect login or password')
    
    return SuccessLogin(status='success', api_key=settings.api_key)