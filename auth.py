from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_db_and_tables
from routes import router

@asynccontextmanager
async def lifespan(app :FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(router)