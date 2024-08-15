from fastapi import APIRouter, HTTPException, Depends, Query
from asyncpg import Connection
import uuid

from depends import api_key_auth
from database import get_db_connection


author_router = APIRouter(
    prefix='/authors',
    tags=['Authors']
)


@author_router.post('', dependencies=[Depends(api_key_auth)])
async def create_author(
    author_name: str,
    connection: Connection = Depends(get_db_connection)
):
    query = "INSERT INTO Authors (author_name) VALUES ($1) RETURNING id_author"
    new_id_author = await connection.fetchval(query, author_name)
    return {
        "status": "success", 
        'id_author': new_id_author
    }


@author_router.get('', dependencies=[Depends(api_key_auth)])
async def get_authors(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    desc: bool = Query(False, description="Sort in descending order"),
    connection: Connection = Depends(get_db_connection)
):
    query = "SELECT id_author, author_name FROM Authors ORDER BY author_name"
    if desc:
        query += ' DESC'
    query += f" OFFSET {offset} LIMIT {limit}"
    authors = await connection.fetch(query)
    
    return {
        'authors': authors,
        'next_from': None if len(authors) < limit else offset + limit,
        'count': len(authors)
    }


@author_router.get('/{id_author}', dependencies=[Depends(api_key_auth)])
async def get_author(
    id_author: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    query = "SELECT id_author, author_name FROM Authors WHERE id_author = $1 LIMIT 1"
    author = await connection.fetchrow(query, id_author)
    
    return {
        'author': author,
    }


@author_router.put('/{id_author}', dependencies=[Depends(api_key_auth)])
async def update_author(
    id_author: uuid.UUID,
    author_name: str,
    connection: Connection = Depends(get_db_connection)
):
    query = "UPDATE Authors SET author_name = $1 WHERE id_author = $2"
    await connection.execute(query, author_name, id_author)
    return {
        'status': 'success',
        'id_author': id_author 
    }
