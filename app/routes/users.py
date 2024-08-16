from fastapi import APIRouter, HTTPException, Depends, Query, Path
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
    sort_by: str = Query("full_name", regex="^(full_name|address)$"),
    desc: bool = Query(False, description="Sorting"),
    connection: Connection = Depends(get_db_connection)
):
    order = "DESC" if desc else "ASC"
    query = f'''SELECT id_user, full_name, birth_date, address, phone_number 
    FROM users ORDER BY {sort_by} {order} 
    LIMIT $1 OFFSET $2'''
    
    users = await connection.fetch(query, limit, offset)
    return {
        'users': users,
        'next_from': None if len(users) < limit else offset + limit,
        'count': len(users)
    }


@user_router.get('/id', dependencies=[Depends(api_key_auth)])
async def get_user(
    id_user: uuid.UUID = Query(description='uuid'),
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_user, full_name, birth_date, address, phone_number FROM users 
    WHERE id_user = $1 
    LIMIT 1;
    '''
    user = await connection.fetchrow(query, id_user)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found!")

    return {
        'user': user
    }


@user_router.get('/phone', dependencies=[Depends(api_key_auth)])
async def get_user_by_phone(
    phone_number: str = Query(regex='^7[0-9]{10}$'),
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_user, full_name, birth_date, address FROM users 
    WHERE phone_number = $1 
    LIMIT 1;
    '''
    user = await connection.fetchrow(query, phone_number)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found!")

    return {
        'user': user
    }


@user_router.post('', dependencies=[Depends(api_key_auth)])
async def create_user(
    user: UserCreate,
    connection: Connection = Depends(get_db_connection)
):
    query = """
    INSERT INTO Users (full_name, birth_date, address, phone_number, created_at, updated_at)
    VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    RETURNING id_user;
    """
    
    try:
        new_id_user = await connection.fetchval(query, user.full_name, user.birth_date, user.address, user.phone_number)
        return UserSuccess(
            id_user=new_id_user,
            status='success'
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error with adding user: {str(e)}")
    

@user_router.put('/id', dependencies=[Depends(api_key_auth)])
async def update_user(
    user_id: uuid.UUID,
    user: UserUpdate,
    connection: Connection = Depends(get_db_connection)
):
    query = """
    UPDATE Users 
    SET full_name = $2, 
        birth_date = $3, 
        address = $4, 
        phone_number = $5,
        updated_at = CURRENT_TIMESTAMP
    WHERE id_user = $1;
    """
    
    try:
        await connection.execute(query, user_id, user.full_name, user.birth_date, user.address, user.phone_number)
        return UserSuccess(
            id_user=user_id,
            status='success'
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error with updating user: {str(e)}")