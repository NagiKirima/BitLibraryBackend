import asyncpg
from typing import AsyncGenerator
from settings import settings


async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    connection = await asyncpg.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name
    )
    try:
        yield connection
    finally:
        await connection.close()


async def db_init():
    with open("app/sql/init.sql", "r") as file:
        sql_script = file.read()

    async for connection in get_db_connection():
        await connection.execute(sql_script)


async def db_seeder():
    with open("app/sql/seeder.sql", "r") as file:
        sql_script = file.read()

    async for connection in get_db_connection():
        await connection.execute(sql_script)
