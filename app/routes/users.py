from fastapi import APIRouter, HTTPException, Depends, Query
from asyncpg import Connection
import uuid

from depends import api_key_auth
from database import get_db_connection
from schemas import UserCreate, UserSuccess, UserUpdate


user_router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@user_router.get('', dependencies=[Depends(api_key_auth)])
async def get_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    sort_by: str = Query('', regex="^(|full_name|address)$"),
    desc: bool = Query(False, description="Sorting"),
    connection: Connection = Depends(get_db_connection)
):
    order = " DESC " if desc else " ASC "
    query = f'''SELECT id_user, full_name, birth_date, address, phone_number FROM Users '''
    if sort_by != '':
        query += f'ORDER BY {sort_by} {order}'
    query += 'LIMIT $1 OFFSET $2'
    users = await connection.fetch(query, limit, offset)

    query_total_count = 'SELECT COUNT(*) FROM Users'
    total_count = await connection.fetchval(query_total_count)
    
    return {
        'users': users,
        'next_from': None if len(users) < limit else offset + limit,
        'count': len(users),
        'total_count': total_count,
        'total_pages': (total_count + limit - 1) // limit
    }


@user_router.get('/id', dependencies=[Depends(api_key_auth)])
async def get_user(
    id_user: uuid.UUID = Query(description='uuid'),
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_user, full_name, birth_date, address, phone_number FROM Users WHERE id_user = $1 LIMIT 1'''
    user = await connection.fetchrow(query, id_user)

    return {
        'user': user
    }


@user_router.delete('/id', dependencies=[Depends(api_key_auth)])
async def delete_user(
    id_user: uuid.UUID = Query(),
    connection: Connection = Depends(get_db_connection)
):
    query = '''DELETE FROM Users WHERE id_user = $1'''
    await connection.execute(query, id_user)

    return {
        "status": "success"
    }


@user_router.get('/phone', dependencies=[Depends(api_key_auth)])
async def get_user_by_phone(
    phone_number: str = Query(regex='^7[0-9]{10}$'),
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_user, full_name, birth_date, address FROM Users WHERE phone_number = $1 LIMIT 1'''
    user = await connection.fetchrow(query, phone_number)
   
    return {
        'user': user
    }


@user_router.post('', dependencies=[Depends(api_key_auth)])
async def create_user(
    user: UserCreate,
    connection: Connection = Depends(get_db_connection)
):
    query = """
        INSERT INTO Users (full_name, birth_date, address, phone_number)
        VALUES ($1, $2, $3, $4)
        RETURNING id_user
    """
    
    new_id_user = await connection.fetchval(query, user.full_name, user.birth_date, user.address, user.phone_number)
    
    return UserSuccess(
        id_user=new_id_user,
        status='success'
    )
    

@user_router.patch('/id', dependencies=[Depends(api_key_auth)])
async def update_user(
    id_user: uuid.UUID,
    user: UserUpdate,
    connection: Connection = Depends(get_db_connection)
):
    query = """UPDATE Users SET full_name = $2, birth_date = $3, address = $4 WHERE id_user = $1"""
    
    await connection.execute(query, id_user, user.full_name, user.birth_date, user.address)
    return UserSuccess(
        id_user=id_user,
        status='success'
    )
