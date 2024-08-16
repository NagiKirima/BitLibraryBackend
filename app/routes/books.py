from fastapi import APIRouter, HTTPException, Depends, Query
from asyncpg import Connection
from typing import List, Optional
import uuid

from depends import api_key_auth
from schemas import BookCreate, BookUpdate, BookBorrow
from database import get_db_connection


book_router = APIRouter(
    prefix='/books',
    tags=['Books']
)


@book_router.get('/books/status/id', dependencies=[Depends(api_key_auth)])
async def get_book_status_by_id(
    id_book: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    query = '''
    SELECT BookDetails.id_book, BookDetails.title, 
    array_agg(DISTINCT BookDetails.author_name) AS authors, 
    array_agg(DISTINCT BookDetails.genre_name) AS genres,
    COALESCE(last_borrow.is_returned, TRUE) AS is_available,
    last_borrow.id_user AS id_user
    FROM BookDetails 
    LEFT JOIN (
        SELECT br.id_book, br.return_date, br.is_returned, br.id_user 
        FROM BorrowReturnLogs br
        WHERE (br.id_book, br.return_date) IN (
            SELECT id_book, MAX(return_date)
            FROM BorrowReturnLogs
            GROUP BY id_book
        )
    ) AS last_borrow ON BookDetails.id_book = last_borrow.id_book 
    WHERE BookDetails.id_book = $1 
    GROUP BY BookDetails.id_book, BookDetails.title, last_borrow.is_returned, last_borrow.id_user 
    ORDER BY BookDetails.id_book 
    '''

    book = await connection.fetchrow(query, id_book)

    return {
        'book': book
    }


@book_router.get('/books/status', dependencies=[Depends(api_key_auth)])
async def get_books_by_returned_status(
    status: bool = True,
    desc: bool = Query(True),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    connection: Connection = Depends(get_db_connection)
):
    order_by = " DESC" if desc else " ASC"
    query = f'''
    SELECT BookDetails.id_book, BookDetails.title, 
    array_agg(DISTINCT BookDetails.author_name) AS authors, 
    array_agg(DISTINCT BookDetails.genre_name) AS genres,
    COALESCE(last_borrow.is_returned, TRUE) AS is_available,
    last_borrow.id_user AS id_user 
    FROM BookDetails 
    LEFT JOIN (
        SELECT br.id_book, br.return_date, br.is_returned, br.id_user
        FROM BorrowReturnLogs br
        WHERE (br.id_book, br.return_date) IN (
            SELECT id_book, MAX(return_date)
            FROM BorrowReturnLogs
            GROUP BY id_book
        )
    ) AS last_borrow ON BookDetails.id_book = last_borrow.id_book
    WHERE COALESCE(last_borrow.is_returned, TRUE) = $1
    GROUP BY BookDetails.id_book, BookDetails.title, last_borrow.is_returned, last_borrow.id_user 
    ORDER BY BookDetails.title {order_by}
    OFFSET $2 LIMIT $3
    '''

    books = await connection.fetch(query, status, offset, limit)
    
    return {
        'books': books,
        'next_from': None if len(books) < limit else offset + limit,
        'count': len(books)
    }


@book_router.get('', dependencies=[Depends(api_key_auth)])
async def get_books(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    sort_by: str = Query("", regex="^(|title$)"),
    desc: bool = Query(False),
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_book, title, 
    array_agg(DISTINCT author_name) AS authors, 
    array_agg(DISTINCT genre_name) AS genres 
    FROM BookDetails
    GROUP BY id_book, title
    '''
    if sort_by != "":
        query += f" ORDER BY {sort_by}"
        query += " DESC" if desc else " ASC"
    
    query += f" OFFSET {offset} LIMIT {limit}"

    books = await connection.fetch(query)
    
    return {
        'books': books,
        'next_from': None if len(books) < limit else offset + limit,
        'count': len(books)
    }


@book_router.get('/id', dependencies=[Depends(api_key_auth)])
async def get_book(
    id_book: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_book, title, 
    array_agg(DISTINCT author_name) AS authors, 
    array_agg(DISTINCT genre_name) AS genres 
    FROM BookDetails
    WHERE id_book = $1 
    GROUP BY id_book, title 
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


@book_router.put('/id', dependencies=[Depends(api_key_auth)])
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


@book_router.get('/borrows', dependencies=[Depends(api_key_auth)])
async def get_borrows(
    id_user: Optional[str] = None,
    id_book: Optional[str] = None,
    is_returned: Optional[bool] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, ge=0),
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_borrow, id_user, id_book, is_returned, borrow_date, return_date FROM BorrowReturnLogs'''
    query_params = {}
    
    if id_user is not None:
        query_params['id_user'] = id_user
    if id_book is not None:
        query_params['id_book'] = id_book
    if is_returned is not None:
        query_params['is_returned'] = is_returned
    

    where_conditions = " AND ".join([f"{key} = ${i+1}" for i, key in enumerate(query_params.keys())])
    if where_conditions:
        query += f" WHERE {where_conditions}"
    
    query += f' OFFSET {offset} LIMIT {limit}'

    borrows = await connection.fetch(query, *query_params.values())
    return {
        'borrows': borrows,
        'next_from': None if len(borrows) < limit else offset + limit,
        'count': len(borrows)
    }
    

@book_router.get('/borrows/id', dependencies=[Depends(api_key_auth)])
async def get_borrow(
    id_borrow: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_borrow, id_user, id_book, is_returned, borrow_date, return_date FROM BorrowReturnLogs 
    WHERE id_borrow = $1
    '''

    borrow = await connection.fetchrow(query, id_borrow)
    
    return {
        'borrow': borrow,
    }


@book_router.post('/borrows', dependencies=[Depends(api_key_auth)])
async def add_borrow(
    book_borrow: BookBorrow,
    connection: Connection = Depends(get_db_connection)
):
    query = '''
        INSERT INTO BorrowReturnLogs (id_user, id_book, borrow_date, return_date) 
        VALUES ($1, $2, $3, $4)
        RETURNING id_borrow
        '''
    new_log_id = await connection.fetchval(query, book_borrow.id_user, book_borrow.id_book, book_borrow.borrow_date, book_borrow.return_date)

    return {
        'status': 'success',
        'id_borrow': new_log_id
    }


@book_router.patch('/borrows/id', dependencies=[Depends(api_key_auth)])
async def change_borrow_status(
    id_borrow: uuid.UUID,
    status: bool = True,
    connection: Connection = Depends(get_db_connection)
):
    query = "UPDATE BorrowReturnLogs SET is_returned = $1 WHERE id_borrow = $2"
    await connection.execute(query, status, id_borrow)

    return {
        'status': 'success',
        'id_borrow': id_borrow
    }