from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response, Cookie, status, Depends
from datetime import datetime, timedelta, timezone
from config import settings
import traceback
from models import AccessToken, UserInDB, User, RefreshToken
from dependencies import SessionDep, FormDataDep, UserDep, require_role
from database import (get_user, add_user, get_refresh_token, add_refresh_token, 
                      delete_refresh_token, set_refresh_token_expire_date, 
                      enforce_session_limit, create_db_and_tables)
from typing import Annotated
from security import (verify_password, create_access_token, 
                      generate_refresh_token_string)
from schemas import to_form_user

@asynccontextmanager
async def lifespan(app :FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "Welcome to my basic FastAPI service!"}


@app.post("/register")
def register(
    # здесь класс OAuth2PasswordRequestForm показывает, что питону нужно брать данные не из query-параметров или body:json, а из body:form-data.
    form_data: FormDataDep,
    response: Response,
    session: SessionDep
) -> AccessToken:
    if get_user(session, form_data.username):
        raise HTTPException(status_code=400, detail="User with such email already exists")

    user = to_form_user(form_data)
    try:
        add_user(session, user)
    except Exception:
        raise HTTPException(status_code=400, detail="Something went wrong while trying to add user to database")
    
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token({"sub": form_data.username}, expires_delta)
    
    refresh_token_value = generate_refresh_token_string()
    expiration_date = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = RefreshToken(username = form_data.username, token=refresh_token_value, expires_at=expiration_date)
    try:
        add_refresh_token(session, refresh_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Something went wrong while trying to add refresh token to database")

    response.set_cookie(
        key = "refresh_token",
        value = refresh_token_value,
        httponly=True,
        secure=False, ##########!!!!!!!! чтобы Cookie передавались по http. в deployment обязательно сделать True.
        samesite="lax",
        expires=60*60*24*90
    )

    return AccessToken(access_token=access_token, token_type="bearer")

@app.post("/token")
def login( # чтобы система преобразовала объект FormData в json
    # здесь класс OAuth2PasswordRequestForm показывает, что питону нужно брать данные не из query-параметров или body:json, а из body:form-data.
    form_data: FormDataDep,
    response: Response,
    session: SessionDep
) -> AccessToken:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = get_user(session, form_data.username)
    if not user:
        raise credentials_exception
    
    hashed_password = user.hashed_password
    is_correct_password = verify_password(
        form_data.password,
        hashed_password,
    )

    if not is_correct_password:
        raise credentials_exception
    
    enforce_session_limit(session, user.username)

    refresh_token_value = generate_refresh_token_string()
    expiration_date = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = RefreshToken(username = user.username, token=refresh_token_value, expires_at=expiration_date)
    add_refresh_token(session, refresh_token)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub": user.username}, expires_delta = access_token_expires
    )


    response.set_cookie(
        key = "refresh_token",
        value = refresh_token_value,
        httponly=True,
        secure=False, ##########!!!!!!!! чтобы Cookie передавались по http. в deployment обязательно сделать True.
        samesite="lax",
        expires=60*60*24*90
    )

    return AccessToken(access_token=access_token, token_type="bearer")

@app.post("/logout")
def logout(session: SessionDep, response: Response, refresh_token: str = Cookie(None)):
    logout_exception = HTTPException(status_code=404, detail="User is not logged in")
    if not refresh_token:
        raise logout_exception
    delete_refresh_token(session, refresh_token)
    response.delete_cookie(
        key = "refresh_token",
        domain=None,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return {"details": "logged out"}


# oauth2_scheme ищет в запросе заголовок с именем Authorization.
# Проверяет, начинается ли его значение со слова Bearer. Если 
# заголовка нет или он пустой, FastAPI автоматически, даже не 
# доходя до тела вашей функции, возвращает клиенту ошибку 
# 401 Unauthorized с текстом "Not authenticated".

# !!!! Если token есть - oauth2_scheme просто парсит header 
# и берет оттуда token. Оно не проверят протух ли он и есть 
# ли вообще пользователь с таким token. 
# Поэтому для проверки зареган ли пользователь нужен UserDep
# Он уже как раз проверяет залогинен ли пользователь.

# access_token содержиться в header чтобы защитить запрос от 
# перехвата и соответствовать REST-архитектуре
@app.get("/get_current_user", response_model = User)
def get_me(user: UserDep) -> UserInDB:
    return user


@app.post("/api/refresh")
def refresh_session(session: SessionDep, refresh_token: str = Cookie(None)):
    session_expired_exc = HTTPException(status_code=404, detail="Session expired. Log in again please.")

    if not refresh_token:
        raise session_expired_exc
        
    token_data = get_refresh_token(session, refresh_token)
    if not token_data:
        raise session_expired_exc

    if datetime.now(timezone.utc) > token_data.expires_at:
        delete_refresh_token(session, token_data)
        raise session_expired_exc
 
    token_data.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS) 
    try:
        set_refresh_token_expire_date(session, token_data)
    except Exception:
        raise HTTPException(status_code=404, detail="Something went wrong. Please try again later.")
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data = {"sub": token_data.username}, expires_delta=expires_delta
    )

    return AccessToken(access_token=new_access_token, token_type="bearer")

@app.get("/my_information", response_model = User)
def get_my_information(user: Annotated[UserInDB, Depends(require_role("user"))]):
    return user