from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager


from database import db_init, db_seeder
from routes import (auth_router, user_router, book_router, genre_router, author_router)



@asynccontextmanager
async def lifespan(app: FastAPI):
    ''' app startup '''
    await db_init()
    await db_seeder()
    yield
    ''' app shutdown '''


app = FastAPI(title='Library API', lifespan=lifespan)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(book_router)
app.include_router(genre_router)
app.include_router(author_router)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000, log_level='info')