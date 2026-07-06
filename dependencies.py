from typing import Annotated
from fastapi import HTTPException, status 
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends
from sqlmodel import Session
from database import engine
from models import UserInDB
from models import TokenData
import jwt
from config import settings
from jwt.exceptions import InvalidTokenError
from database import get_user

def get_session():
    with Session(engine) as session:
        yield session




SessionDep = Annotated[Session, Depends(get_session)]
FormDataDep = Annotated[OAuth2PasswordRequestForm, Depends()]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
TokenDep = Annotated[str, Depends(oauth2_scheme)]

def require_role(*args: str):
    def dependency(user: UserDep) -> UserInDB:
        if user.role not in list(args):
            raise HTTPException(status_code=400, detail="Insufficient permissions")
        return user
    return dependency # возвращает функцию dependency. Depends() способна вызвать эту возвращаемую функцию.

def get_current_user(
    token: TokenDep,
    session: SessionDep, 
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    ) 

    try:
        # декодирует данные, зашифрованные внутри jwt, и проверяет не истек ли токен
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError: # токен протух
        raise credentials_exception
    
    user = get_user(session, token_data.username)
    if not user:
        raise credentials_exception
    return user


UserDep = Annotated[UserInDB, Depends(get_current_user)]

