from fastapi.security import OAuth2PasswordRequestForm

from models import UserInDB
from security import encrypt_password

def to_form_user(form_data: OAuth2PasswordRequestForm) -> UserInDB:
    username = form_data.username.lower()
    hashed_password = encrypt_password(form_data.password)
    user = UserInDB(username=username, hashed_password=hashed_password, role="user")
    return user