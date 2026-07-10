from typing import Annotated
from fastapi import HTTPException, status 
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import engine
from models import UserInDB
import jwt
from config import settings
from jwt.exceptions import InvalidTokenError
from database import get_user
from exceptions import InvalidCredentialsException, TokenExpiredException

async def get_session():
    async with AsyncSession(engine, expire_on_commit = False) as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]
FormDataDep = Annotated[OAuth2PasswordRequestForm, Depends()]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
TokenDep = Annotated[str, Depends(oauth2_scheme)]

def require_role(*args: str):
    def dependency(user: UserDep) -> UserInDB:
        if user.role not in list(args):
            raise HTTPException(status_code=400, detail="Insufficient permissions")
        return user
    return dependency # возвращает функцию dependency при инициализации require_role, но не вызывает её.
    # dependency внутри require_role вызывается уже при помощи Depends()

async def get_current_user(
    token: TokenDep,
    session: SessionDep, 
) -> UserInDB:


    try:
        # декодирует данные, зашифрованные внутри jwt, и проверяет не истек ли токен
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]) # если токен протух - функция выкинет InvalidTokenError 
    except InvalidTokenError: # токен протух
        raise TokenExpiredException
        
    username = payload.get("sub")
    if username is None:
        raise InvalidTokenError
    
    user = await get_user(session, username)
    if not user:
        raise InvalidCredentialsException
    return user


UserDep = Annotated[UserInDB, Depends(get_current_user)]

