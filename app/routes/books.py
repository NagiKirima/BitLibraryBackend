from fastapi import APIRouter, HTTPException, Depends, Query, Header
from asyncpg import Connection
from typing import List
import uuid

from depends import api_key_auth
from schemas import BookCreate, BookUpdate
from database import get_db_connection


book_router = APIRouter(
    prefix='/books',
    tags=['Books']
)


@book_router.get('', dependencies=[Depends(api_key_auth)])
async def get_books(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    sort_by: str = Query("title", regex="^(title|author_name|genre_name)$", description="Field to sort by: title, author_name, genre_name"),
    desc: bool = Query(False, description="Sort in descending order"),
    is_available: bool = Query(None, description="Filter by is_available"),
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_book, title, is_available, 
    array_agg(DISTINCT author_name) AS authors, 
    array_agg(DISTINCT genre_name) AS genres 
    FROM BookDetails
    '''

    if is_available is not None:
        query += f" WHERE is_available = {is_available}"

    query += " GROUP BY id_book, title, is_available"  
    query += f" ORDER BY {sort_by}"
    if desc:
        query += " DESC"
    query += f" OFFSET {offset} LIMIT {limit}"

    books = await connection.fetch(query)
    
    return {
        'books': books,
        'next_from': None if len(books) < limit else offset + limit,
        'count': len(books)
    }


@book_router.get('/{id_book}', dependencies=[Depends(api_key_auth)])
async def get_books(
    id_book: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_book, title, is_available, 
    array_agg(DISTINCT author_name) AS authors, 
    array_agg(DISTINCT genre_name) AS genres 
    FROM BookDetails
    WHERE id_book = $1
    GROUP BY id_book, title, is_available
    LIMIT 1
    '''    
    book = await connection.fetchrow(query, id_book)
    
    return {
        'book': book,
    }


@book_router.post('', dependencies=[Depends(api_key_auth)])
async def create_book(
    book: BookCreate,
    connection: Connection = Depends(get_db_connection)
):
    async with connection.transaction():
        create_book_query = '''
        INSERT INTO Books (title) 
        VALUES ($1)
        RETURNING id_book
        '''
        new_book_id = await connection.fetchval(create_book_query, book.title)

        for author_id in book.author_ids:
            create_book_author_query = '''
            INSERT INTO BookAuthors (id_book, id_author) 
            VALUES ($1, $2)
            '''
            await connection.execute(create_book_author_query, new_book_id, author_id)

        for genre_id in book.genre_ids:
            create_book_genre_query = '''
            INSERT INTO BookGenres (id_book, id_genre) 
            VALUES ($1, $2)
            '''
            await connection.execute(create_book_genre_query, new_book_id, genre_id)

    return {
        'status': 'success',
        'id_book': new_book_id
    }


@book_router.put('/{id_book}', dependencies=[Depends(api_key_auth)])
async def update_book(
    id_book: uuid.UUID,
    updated_book: BookUpdate,
    connection: Connection = Depends(get_db_connection)
):
    async with connection.transaction():
        update_book_query = '''
        UPDATE Books 
        SET title = $1
        WHERE id_book = $2
        '''
        await connection.execute(update_book_query, updated_book.title, id_book)
        
        # update authors
        delete_book_authors_query = '''
        DELETE FROM BookAuthors 
        WHERE id_book = $1
        '''
        await connection.execute(delete_book_authors_query, id_book)
        
        for author_id in updated_book.author_ids:
            create_book_author_query = '''
            INSERT INTO BookAuthors (id_book, id_author) 
            VALUES ($1, $2)
            '''
            await connection.execute(create_book_author_query, id_book, author_id)
        
        # update genres
        delete_book_genres_query = '''
        DELETE FROM BookGenres 
        WHERE id_book = $1
        '''
        await connection.execute(delete_book_genres_query, id_book)
        
        for genre_id in updated_book.genre_ids:
            create_book_genre_query = '''
            INSERT INTO BookGenres (id_book, id_genre) 
            VALUES ($1, $2)
            '''
            await connection.execute(create_book_genre_query, id_book, genre_id)
    
    return {
        "status": "success",
        'id_book': id_book
    }