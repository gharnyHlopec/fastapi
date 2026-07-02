from pydantic import BaseModel, field_serializer
from sqlmodel import SQLModel, Field 
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone

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

    created_at: datetime = Field(
        default_factory = lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory= lambda: datetime.now(timezone.utc), 
        sa_column_kwargs= {"onupdate": lambda: datetime.now(timezone.utc)} # при каждом session.commit()
        # для данного пользователя дата обновляется
    )


class User(BaseModel):
    username: str = Field(index = True)
    created_at: datetime

    # вызывается при конвертированнии данных в json перед передачей на frontend
    @field_serializer("created_at")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.strftime("%d.%m.%Y %H:%M:%S")

class RefreshToken(SQLModel, table = True):
    id: int | None = Field(default = None, primary_key=True)
    token: str
    username: str = Field(index = True)
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True))
    )