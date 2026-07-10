import bcrypt
from config import settings
import jwt
from datetime import datetime, timedelta, timezone
import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def encrypt_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

    
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    to_encode['exp'] = datetime.now(timezone.utc) + expires_delta
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def generate_refresh_token_string() -> str:
    """Генерирует уникальную безопасную строку для базы данных"""
    return secrets.token_urlsafe(64)
