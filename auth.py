from contextlib import asynccontextmanager
from fastapi import FastAPI
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

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(router)