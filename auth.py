from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from logger import setup_logging
import logging

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded



@asynccontextmanager
async def lifespan(app :FastAPI):
    yield

setup_logging()
logger = logging.getLogger("app")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # чтобы можно было с этого ip отправлять запросы на сервер
    allow_origins=['http://localhost:3000'],
    allow_credentials=True, # позволяет использовать cookie (в них хранится refresh token)
    allow_methods=["*"], 
    allow_headers=["*"]
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(router)