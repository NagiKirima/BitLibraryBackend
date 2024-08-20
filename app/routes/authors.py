from fastapi import APIRouter, HTTPException, Depends, Query, Body
from asyncpg import Connection
import uuid

from depends import api_key_auth
from database import get_db_connection
from schemas import AuthorCreate, AuthorEdit


author_router = APIRouter(
    prefix='/authors',
    tags=['Authors']
)


@author_router.post('', dependencies=[Depends(api_key_auth)])
async def create_author(
    author: AuthorCreate,
    connection: Connection = Depends(get_db_connection)
):
    query = "INSERT INTO Authors (author_name) VALUES ($1) RETURNING id_author"
    new_author_id = await connection.fetchval(query, author.author_name)
    return {
        "status": "success", 
        'id_author': new_author_id
    }


@author_router.get('', dependencies=[Depends(api_key_auth)])
async def get_authors(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    desc: bool = Query(False, description="Sort in descending order"),
    connection: Connection = Depends(get_db_connection)
):
    order_by = ' DESC' if desc else ' ASC'
    query = f"SELECT id_author, author_name FROM Authors ORDER BY author_name {order_by}"
    query += f" OFFSET {offset} LIMIT {limit}"
    authors = await connection.fetch(query)

    total_count_query = 'SELECT COUNT(*) FROM Authors'
    total_count = await connection.fetchval(total_count_query)
    
    return {
        'authors': authors,
        'next_from': None if offset + limit >= total_count else offset + limit,
        'count': len(authors),
        'total_count': total_count,
        'total_pages': (total_count + limit - 1) // limit
    }


@author_router.get('/id', dependencies=[Depends(api_key_auth)])
async def get_author(
    id_author: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    query = "SELECT id_author, author_name FROM Authors WHERE id_author = $1 LIMIT 1"
    author = await connection.fetchrow(query, id_author)
    
    return {
        'author': author,
    }


@author_router.delete('/id', dependencies=[Depends(api_key_auth)])
async def delete_author(
    id_author: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    delete_query = 'DELETE FROM Authors WHERE id_author = $1'
    await connection.execute(delete_query, id_author)
    
    return {"status": "success"}


@author_router.put('/id', dependencies=[Depends(api_key_auth)])
async def update_author(
    id_author: uuid.UUID,
    author: AuthorEdit,
    connection: Connection = Depends(get_db_connection)
):
    query = "UPDATE Authors SET author_name = $1 WHERE id_author = $2"
    await connection.execute(query, author.author_name, id_author)
    return {
        'status': 'success',
        'id_author': id_author 
    }
