from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes import router
from logger import setup_logging
import logging

@asynccontextmanager
async def lifespan(app :FastAPI):
    yield

setup_logging()
logger = logging.getLogger("app")

app = FastAPI(lifespan=lifespan)

app.include_router(router)