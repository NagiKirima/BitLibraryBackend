from fastapi import APIRouter, HTTPException, Depends, Query
from asyncpg import Connection
from geojson import Feature, FeatureCollection, Point
import random
import json

from settings import settings
from depends import api_key_auth
from database import get_db_connection


reports_router = APIRouter(
    prefix='/reports',
    tags=['Reports']
)


@reports_router.get('/books/available', dependencies=[Depends(api_key_auth)])
async def get_availableable_books(
    connection: Connection = Depends(get_db_connection)
):
    query = f'''
        SELECT BookDetails.id_book, COALESCE(last_borrow.is_returned, TRUE) as is_available
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
        WHERE COALESCE(last_borrow.is_returned, TRUE) = TRUE 
        ORDER BY title ASC
    '''
    books = await connection.fetch(query)    
    return {
        'report': {
            'available_books': books
        } 
    }


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
    query = '''SELECT g.genre_name, COUNT(*) AS genre_count
        FROM Books b
        JOIN BookGenres bg ON b.id_book = bg.id_book
        JOIN Genres g ON bg.id_genre = g.id_genre
        JOIN BorrowReturnLogs brl ON b.id_book = brl.id_book
        GROUP BY g.genre_name
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
    query = '''SELECT u.full_name AS full_name, 
        b.title AS book_title, 
        br.borrow_date AS borrow_date,
        br.return_date AS return_date,
        br.is_returned
        FROM BorrowReturnLogs br
        JOIN Users u ON br.id_user = u.id_user
        JOIN Books b ON br.id_book = b.id_book
        WHERE br.is_returned = FALSE AND CURRENT_DATE > br.return_date
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
    query = '''
        SELECT br.id_book,
            br.return_date,
            br.borrow_date,
            CURRENT_DATE as current_date,
            br.id_user,
            u.address, u.phone_number, COALESCE(last_borrow.is_returned, TRUE) as is_returned
        FROM BorrowReturnLogs br
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
        ) AS last_borrow ON br.id_book = last_borrow.id_book 
        JOIN Users u ON br.id_user = u.id_user 
        WHERE COALESCE(last_borrow.is_returned, TRUE) = FALSE
    '''
    if limit is not None:
        query += f'LIMIT {limit}'
    result = await connection.fetch(query)

    # geojson data
    features = [
        Feature(geometry=Point((random.uniform(-180, 180), random.uniform(-90, 90))), 
                properties={ **item }) for item in result
    ]

    return {
        'report': {
            'users_geo': features
        }
    }