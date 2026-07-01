from pydantic import BaseModel
from sqlmodel import SQLModel, Field 
from sqlalchemy import Column, DateTime
from datetime import datetime

class AccessToken(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str

class UserInDB(SQLModel, table = True):
    id: int | None = Field(default = None, primary_key=True)
    username: str = Field(index = True)
    hashed_password: str
    role: str

class User(BaseModel):
    username: str = Field(index = True)

class RefreshToken(SQLModel, table = True):
    id: int | None = Field(default = None, primary_key=True)
    token: str
    username: str = Field(index = True)
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True))
    )