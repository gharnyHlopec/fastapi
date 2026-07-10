from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from logger import setup_logging
import logging

from slowapi import _rate_limit_exceeded_handler
from rate_limiter import limiter

from slowapi.errors import RateLimitExceeded

from fastapi_pagination import add_pagination


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

add_pagination(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(router)