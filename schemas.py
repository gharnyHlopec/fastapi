from fastapi.security import OAuth2PasswordRequestForm

from models import UserBase, UserInDB
from security import encrypt_password
import asyncio

async def to_form_user(form_data: OAuth2PasswordRequestForm) -> UserInDB:
    username = form_data.username.lower()
    validated_user = UserBase(username=username)
    hashed_password = await asyncio.to_thread(encrypt_password, form_data.password)
    user = UserInDB(username=validated_user.username, hashed_password=hashed_password, role="user")
    return user