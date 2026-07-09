from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from database import create_db_and_tables
from routes import router
from pydantic import ValidationError
from logger import setup_logging
from traceback import format_exc

@asynccontextmanager
async def lifespan(app :FastAPI):
    await create_db_and_tables()
    yield

setup_logging()
app = FastAPI(lifespan=lifespan)

app.include_router(router)

# декоратор регистрирует функцию во внутреннем реестре FastAPI/Starlette как обработчик для исключений типа ValidationError.
# похоже на работу @app.get("/users"). функция под этим декоратором сама вызывается, когда происходит event, к которому она привязана 
@app.exception_handler(ValidationError) 
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError): # exc - объект исключения, который был выброшен Python
    errors = exc.errors()
    
    # Формируем сообщение об ошибке, которое будем отправлять на frontend
    formatted_errors = [
        {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"]
        }
        for error in errors
    ]
    
    raise HTTPException(
        status_code=422,
        detail=formatted_errors
    )