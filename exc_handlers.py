from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from auth import app
import logging

logger = logging.getLogger("app")

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
    
    return JSONResponse(
        status_code=422,
        content={"details": formatted_errors}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Occured some exception")

    return JSONResponse(
        status_code=500,
        content={"details": "Internal server error"}
    )