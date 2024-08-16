from fastapi import APIRouter, HTTPException, Depends, Query
from asyncpg import Connection
import uuid

from depends import api_key_auth
from database import get_db_connection


genre_router = APIRouter(
    prefix='/genres',
    tags=['Genres']
)


@genre_router.post('', dependencies=[Depends(api_key_auth)])
async def create_genre(
    genre_name: str,
    connection: Connection = Depends(get_db_connection)
):
    query = "INSERT INTO Genres (genre_name) VALUES ($1) RETURNING id_genre"
    new_id_genre = await connection.fetchval(query, genre_name)
    return {
        "status": "success", 
        'id_genre': new_id_genre
    }


@genre_router.get('', dependencies=[Depends(api_key_auth)])
async def get_genres(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    desc: bool = Query(False, description="Sort in descending order"),
    connection: Connection = Depends(get_db_connection)
):
    order_by = ' DESC' if desc else ' ASC'
    query = f"SELECT id_genre, genre_name FROM Genres ORDER BY genre_name {order_by}"
    query += f" OFFSET {offset} LIMIT {limit}"
    
    genres = await connection.fetch(query)
    
    return {
        'genres': genres,
        'next_from': None if len(genres) < limit else offset + limit,
        'count': len(genres)
    }


@genre_router.get('/id', dependencies=[Depends(api_key_auth)])
async def get_genre(
    id_genre: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    query = "SELECT id_genre, genre_name FROM Genres WHERE id_genre = $1 LIMIT 1"
    genre = await connection.fetchrow(query, id_genre)
    
    return {
        'genre': genre,
    }


@genre_router.put('/id', dependencies=[Depends(api_key_auth)])
async def update_genre(
    id_genre: uuid.UUID,
    genre_name: str,
    connection: Connection = Depends(get_db_connection)
):
    query = "UPDATE Genres SET genre_name = $1 WHERE id_genre = $2"
    await connection.execute(query, genre_name, id_genre)
    return {
        'status': 'success',
        'id_genre': id_genre 
    }
