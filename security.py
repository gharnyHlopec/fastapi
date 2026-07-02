import bcrypt
from config import settings
import jwt
from datetime import datetime, timedelta, timezone
import secrets

def encrypt_password(password: str):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password =  bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')
    return hashed_password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

    
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    to_encode['exp'] = datetime.now(timezone.utc) + expires_delta
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def generate_refresh_token_string() -> str:
    """Генерирует уникальную безопасную строку для базы данных"""
    return secrets.token_urlsafe(64)
