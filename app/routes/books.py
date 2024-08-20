from fastapi import APIRouter, HTTPException, Depends, Query
from asyncpg import Connection
from typing import List, Optional
import uuid
import json

from depends import api_key_auth
from schemas import BookCreate, BookUpdate, BookBorrow
from database import get_db_connection


book_router = APIRouter(
    prefix='/books',
    tags=['Books']
)


@book_router.get('/status/id', dependencies=[Depends(api_key_auth)])
async def get_book_status_by_id(
    id_book: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    query = '''
        SELECT BookDetails.id_book, title, authors, genres, COALESCE(last_borrow.is_returned, TRUE) as is_available FROM BookDetails
        LEFT JOIN (
            SELECT 
                br.id_book, 
                return_date, 
                is_returned, 
                id_user
            FROM BorrowReturnLogs br
            WHERE (br.id_book, br.return_date) IN (
                SELECT id_book, MAX(return_date)
                FROM BorrowReturnLogs
                GROUP BY id_book
            )
        ) AS last_borrow ON BookDetails.id_book = last_borrow.id_book
        WHERE BookDetails.id_book = $1
    '''
    book = await connection.fetchrow(query, id_book)

    if book:
        book_dict = dict(book)
        
        book_dict['authors'] = json.loads(book_dict['authors'])
        book_dict['genres'] = json.loads(book_dict['genres'])
        
        return {'book': book_dict}
    
    return {'book': None}


@book_router.get('/status', dependencies=[Depends(api_key_auth)])
async def get_books_by_status(
    status: bool = True,
    desc: bool = Query(True),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    connection: Connection = Depends(get_db_connection)
):
    order_by = "DESC" if desc else "ASC"
    query = f'''
        SELECT BookDetails.id_book, title, authors, genres, 
        COALESCE(last_borrow.is_returned, TRUE) as is_available
        FROM BookDetails 
        LEFT JOIN (
            SELECT 
                br.id_book, 
                return_date, 
                is_returned, 
                id_user
            FROM BorrowReturnLogs br
            WHERE (br.id_book, br.return_date) IN (
                SELECT id_book, MAX(return_date)
                FROM BorrowReturnLogs
                GROUP BY id_book
            )
        ) AS last_borrow ON BookDetails.id_book = last_borrow.id_book
        WHERE COALESCE(last_borrow.is_returned, TRUE) = $1
        ORDER BY title {order_by}
        OFFSET $2 LIMIT $3;
    '''
    
    books = await connection.fetch(query, status, offset, limit)
    result = []
    for book in books:
        book_dict = dict(book)
        book_dict['authors'] = json.loads(book_dict['authors'])
        book_dict['genres'] = json.loads(book_dict['genres'])
        result.append(book_dict)

    total_count_query = '''
        SELECT COUNT(*)
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
    '''
    total_count = await connection.fetchval(total_count_query, status)
    
    return {
        'books': result,
        'next_from': None if len(books) < limit else offset + limit,
        'total_count': total_count,
        'total_pages': (total_count + limit - 1) // limit
    }


@book_router.get('', dependencies=[Depends(api_key_auth)])
async def get_books(
    id_genre: Optional[str] = None,
    id_author: Optional[str] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    sort_by: str = Query("", regex="^(|title$)"),
    desc: bool = Query(False),
    connection: Connection = Depends(get_db_connection)
):
    query = "SELECT id_book, title, authors, genres FROM BookDetails"
    total_count_query = '''SELECT COUNT(*) FROM BookDetails'''
    
    if id_genre is not None:
        genre_cond = f" WHERE EXISTS (SELECT 1 FROM jsonb_array_elements(genres) genre WHERE (genre->>'id_genre')::uuid = '{id_genre}')"
        query += genre_cond
        total_count_query += genre_cond
        
        if id_author is not None:
            author_cond = f" AND EXISTS (SELECT 1 FROM jsonb_array_elements(authors) author WHERE (author->>'id_author')::uuid = '{id_author}')"
            query += author_cond 
            total_count_query += author_cond

    elif id_author is not None:
        author_cond = f" WHERE EXISTS (SELECT 1 FROM jsonb_array_elements(authors) author WHERE (author->>'id_author')::uuid = '{id_author}')"
        query += author_cond 
        total_count_query += author_cond

    
    if sort_by != "":
        query += f" ORDER BY {sort_by}" 
        query += " DESC" if desc else " ASC" 
    
    query += f" OFFSET {offset} LIMIT {limit}" 
    
    books = await connection.fetch(query)
    total_count = await connection.fetchval(total_count_query)
    
    result = []
    for book in books:
        book_dict = dict(book)
        book_dict['authors'] = json.loads(book_dict['authors'])
        book_dict['genres'] = json.loads(book_dict['genres'])
        result.append(book_dict)

    return {
        'books': result,
        'next_from': None if offset + limit >= total_count else offset + limit,
        'total_count': total_count,
        'total_pages': (total_count + limit - 1) // limit
    }


@book_router.get('/id', dependencies=[Depends(api_key_auth)])
async def get_book(
    id_book: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    query = '''
        SELECT id_book, title, authors, genres FROM BookDetails WHERE id_book = $1
    '''
    book = await connection.fetchrow(query, id_book)

    if book:
        book_dict = dict(book)
        
        book_dict['authors'] = json.loads(book_dict['authors'])
        book_dict['genres'] = json.loads(book_dict['genres'])
        
        return {'book': book_dict}
    
    return {'book': None}


@book_router.delete('/id', dependencies=[Depends(api_key_auth)])
async def delete_book(
    id_book: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    delete_query = 'DELETE FROM Books WHERE id_book = $1'
    await connection.execute(delete_query, id_book)
    
    return {"status": "success"}


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
    sort_by: str =  Query("", regex="^(|borrow_date|return_date$)"),
    desc: bool = Query(default=True),
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
    
    if sort_by:
        order_by = " DESC" if desc else " ASC"
        query += f" ORDER BY {sort_by} {order_by}"
    
    query += f' OFFSET {offset} LIMIT {limit}'
    borrows = await connection.fetch(query, *query_params.values())
    

    total_count_query = '''SELECT COUNT(*) FROM BorrowReturnLogs'''
    if where_conditions:
        total_count_query += f" WHERE {where_conditions}"
    total_count = await connection.fetchval(total_count_query, *query_params.values())

    
    return {
        'borrows': borrows,
        'next_from': None if offset + limit >= total_count else offset + limit,
        'count': len(borrows),
        'total_count': total_count,
        'total_pages': (total_count + limit - 1) // limit
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


@book_router.delete('/borrows/id', dependencies=[Depends(api_key_auth)])
async def delete_borrow(
    id_borrow: uuid.UUID,
    connection: Connection = Depends(get_db_connection)
):
    query = '''DELETE FROM BorrowReturnLogs WHERE id_borrow = $1'''
    await connection.execute(query, id_borrow)
    
    return {
        'status': 'success',
    }


@book_router.post('/borrows', dependencies=[Depends(api_key_auth)])
async def add_borrows(
    id_user: uuid.UUID,
    books_borrows: BookBorrow,
    connection: Connection = Depends(get_db_connection)
):
    async with connection.transaction():
        for ids_books in books_borrows.books_ids:
            query = '''
                INSERT INTO BorrowReturnLogs (id_user, id_book, borrow_date, return_date) 
                VALUES ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING
                '''
            await connection.execute(query, id_user, ids_books, books_borrows.borrow_date, books_borrows.return_date)

    return {
        'status': 'success',
    }


@book_router.patch('/borrows/id', dependencies=[Depends(api_key_auth)])
async def change_borrow_status(
    id_borrow: uuid.UUID,
    status: bool = Query(default=True),
    connection: Connection = Depends(get_db_connection)
):
    query = "UPDATE BorrowReturnLogs SET is_returned = $1 WHERE id_borrow = $2"
    await connection.execute(query, status, id_borrow)

    return {
        'status': 'success',
        'id_borrow': id_borrow
    }
