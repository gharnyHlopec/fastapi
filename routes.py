from fastapi import (HTTPException, Response, Cookie, status, Depends,
                     APIRouter, Query)
from datetime import datetime, timedelta, timezone
from config import settings
import traceback
from models import AccessToken, UserInDB, UserOutput, RefreshToken
from dependencies import SessionDep, FormDataDep, UserDep, require_role
from database import (get_user, add_user, get_refresh_token, add_refresh_token, 
                      delete_refresh_token, set_refresh_token_expire_date, 
                      get_particular_user, get_particular_users, 
                      enforce_session_limit)
from typing import Annotated, Literal
from security import (verify_password, create_access_token, 
                      generate_refresh_token_string)
from schemas import to_form_user

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "Welcome to my basic FastAPI service!"}


@router.post("/register", response_model = AccessToken)
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

@router.post("/token", response_model = AccessToken)
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

@router.post("/logout")
def logout(
    session: SessionDep,
    response: Response, 
    refresh_token: str = Cookie(None)
):
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

@router.post("/api/refresh", response_model=AccessToken)
def refresh_session(
    session: SessionDep,
    refresh_token: str = Cookie(None)
) -> AccessToken:
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

@router.get("/users/me", response_model = UserOutput)
def get_my_information(user: Annotated[UserInDB, Depends(require_role("user", "admin"))]):
    return user

@router.get("/users/{user_id}", response_model = UserOutput)
def particular_user(
    user_id: int, 
    session: SessionDep,
    user: Annotated[UserInDB, Depends(require_role("admin"))],
) -> UserInDB | None:
    requested_user = get_particular_user(session, user_id)
    if requested_user is None:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found"
        )
    return requested_user

@router.get("/users", response_model = list[UserOutput])
def users(
    user: Annotated[
        UserInDB, 
        Depends(require_role("admin"))
    ],
    session: SessionDep,
    username_substring: Annotated[
        str | None, 
        Query(
            examples = ["user"],
            description = "Подстрока для поиска пользователей по части username'а"
        )
    ] = None,
    limit: Annotated[
        int | None, 
        Query(
            examples = [1],
            gt=0, 
            description = "Максимальное возвращаемое количество записей"
        )
    ] = None,
    sort_by: Annotated[
        Literal["username", "created_at"],
        Query(
            examples = ["username"],
            description = "По какому полю сортировать"
        )
    ] = "username",
    sort_order: Annotated[
        Literal["asc", "desc"],
        Query(
            examples = ["asc"],
            description = "В каком порядке отображать записи"
            )
    ] = "asc"
) -> list[UserInDB]:
    users = get_particular_users(session, username_substring, limit, sort_by, sort_order)
    return users