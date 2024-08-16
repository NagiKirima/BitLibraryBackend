from fastapi import APIRouter, HTTPException, Depends, Query
from asyncpg import Connection

from settings import settings
from depends import api_key_auth
from database import get_db_connection


reports_router = APIRouter(
    prefix='/reports',
    tags=['Reports']
)


# todo: add pagination for reports
@reports_router.get('/books/users/all',  dependencies=[Depends(api_key_auth)])
async def get_users_total_borrowed_books(
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_user, COUNT(id_book) AS total_count
        FROM BorrowReturnLogs
        GROUP BY id_user
    '''
    result = await connection.fetch(query)

    return {
        'report': {
            'total_books': result
        }
    }


@reports_router.get('/books/users/current',  dependencies=[Depends(api_key_auth)])
async def get_users_current_borrowed_books(
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_user, COUNT(id_book) AS count
        FROM BorrowReturnLogs
        WHERE is_returned = FALSE
        GROUP BY id_user
    '''
    result = await connection.fetch(query)

    return {
        'report': {
            'current_books': result
        }
    }


@reports_router.get('/visit/last',  dependencies=[Depends(api_key_auth)])
async def get_users_last_visit(
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT id_user, MAX(borrow_date) AS date
        FROM BorrowReturnLogs
        GROUP BY id_user
    '''
    result = await connection.fetch(query)

    return {
        'report': {
            'visits': result
        }
    }


@reports_router.get('/genres/popular',  dependencies=[Depends(api_key_auth)])
async def get_users_borrowed_books(
    limit: int = Query(default=None, gt=0),
    connection: Connection = Depends(get_db_connection)
):
    query = '''SELECT bd.genre_name, COUNT(*) AS genre_count
        FROM BookDetails bd
        JOIN BookGenres bg ON bd.id_book = bg.id_book
        JOIN BorrowReturnLogs brl ON bd.id_book = brl.id_book
        GROUP BY bd.genre_name
        ORDER BY genre_count DESC
    '''
    if limit is not None:
        query += f'LIMIT {limit}'
    result = await connection.fetch(query)

    return {
        'report': {
            'genres_top': result
        }
    }


@reports_router.get('/borrows/fine',  dependencies=[Depends(api_key_auth)])
async def get_fine_borrows(
    limit: int = Query(default=None, gt=0),
    connection: Connection = Depends(get_db_connection)
):
    # todo: add more information for frontend xd
    query = '''SELECT u.full_name AS full_name, 
        b.title AS book_title, 
        br.borrow_date AS borrow_date,
        br.return_date AS return_date
        FROM BorrowReturnLogs br
        JOIN Users u ON br.id_user = u.id_user
        JOIN Books b ON br.id_book = b.id_book
        WHERE br.is_returned = FALSE AND NOW() > br.return_date
        ORDER BY br.borrow_date
    '''
    if limit is not None:
        query += f'LIMIT {limit}'
    result = await connection.fetch(query)

    return {
        'report': {
            'borrows': result
        }
    }


@reports_router.get('/borrows/geo',  dependencies=[Depends(api_key_auth)])
async def get_borrowed_users_geo(
    limit: int = Query(default=None, gt=0),
    connection: Connection = Depends(get_db_connection)
):
    # todo: need more info
    query = '''SELECT
        u.full_name AS full_name,
        u.phone_number AS phone,
        u.address AS address,
        b.title AS book_title
        FROM Users u
        JOIN BorrowReturnLogs brl ON u.id_user = brl.id_user
        JOIN Books b ON brl.id_book = b.id_book
    '''
    if limit is not None:
        query += f'LIMIT {limit}'
    result = await connection.fetch(query)

    return {
        'report': {
            'users_geo': result
        }
    }