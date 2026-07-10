from pydantic import BaseModel, field_serializer, EmailStr
from sqlmodel import SQLModel, Field 
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone
from typing import Literal
from enum import Enum

class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class AccessToken(BaseModel):
    access_token: str = Field(
        description = "jwt токен",
        schema_extra = {"example": "JNW54zxJpN0t5e9_VAsKoeEI7edycjtWJWt6_xIiw8nsWNE2YvZvn3HF3nza3TayuLv41O6SjyL4pTLYPE0B8w"}
    )
    token_type: Literal["bearer"] = Field(
        default = "bearer",
        description = "Тип токена. В нашем случае всегда 'bearer'",
        schema_extra = {"example": "bearer"}
    )


    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "JNW54zxJpN0t5e9_VAsKoeEI7edycjtWJWt6_xIiw8nsWNE2YvZvn3HF3nza3TayuLv41O6SjyL4pTLYPE0B8w",
                    "token_type": "bearer"
                }
            ]
        }
    }

class UserBase(BaseModel):
    username: EmailStr = Field(
        index = True,
        description="Уникальный email пользователя",
        schema_extra={"example": "user@gmail.com"}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "useremail@gmail.com",
                }
            ]
        }
    }

class UserOutput(UserBase):
    created_at: datetime = Field(
        description="Дата и время регистрации аккаунта",
        schema_extra={"example": "02.07.2026 15:09:07"}
    )
    # вызывается при конвертированнии данных в json перед передачей на frontend
    @field_serializer("created_at")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.strftime("%d.%m.%Y %H:%M:%S")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "useremail@gmail.com",
                    "created_at": "02.07.2026 15:09:07"
                }
            ]
        }
    }


# при table=True не происходит валидация со стороны pydantic. 
class UserInDB(SQLModel, table = True):
    __tablename__ = 'users'  # Table name in the database

    id: int | None = Field(
        default = None, 
        description="Уникальный id пользователя",
        primary_key=True
    )
    username: EmailStr = Field(
        index = True,
        description="Уникальный email пользователя"
    )
    hashed_password: str = Field(
        description = "Зашифрованный пароль пользователя"
    )
    role: UserRole = Field(
        description="Роль пользователя. Может принимать только значения 'user' и 'admin'"
    )

    created_at: datetime = Field( # удобный высокоуровневый способ описать поле, который автоматически генерирует соответствующую SQLAlchemy-колонку.
        default_factory = lambda: datetime.now(timezone.utc),
        # без sa_column SQLModel бы автоматически установил тип колонки DateTime(timezone=False)
        sa_column = Column( # класс SQLAlchemy, описывающий колонку в БД
            DateTime(timezone=True) # тип данных SQLAlchemy
        ),
        description="Дата и время регистрации аккаунта",
    )

    updated_at: datetime = Field( # удобный высокоуровневый способ описать поле, который автоматически генерирует соответствующую SQLAlchemy-колонку.
        default_factory= lambda: datetime.now(timezone.utc), 
        description="Дата и время изменения записи пользователя, которое происходит через ORM session.commit()",
        # без sa_column SQLModel бы автоматически установил тип колонки DateTime(timezone=False)
        sa_column = Column( # класс SQLAlchemy, описывающий колонку в БД
            DateTime(timezone=True), # тип данных SQLAlchemy
            onupdate = lambda: datetime.now(timezone.utc)
        )
    )



class RefreshToken(SQLModel, table = True):
    __tablename__ = "refresh_tokens"
    
    id: int | None = Field(
        default = None, 
        primary_key=True,
        description="Уникальный идентификатор пользователя"
    )
    token: str = Field(
        description="Jwt токен"
    )
    username: EmailStr = Field(
        index = True,
        description="Уникальный email пользователя"
    )
    expires_at: datetime = Field( # удобный высокоуровневый способ описать поле, который автоматически генерирует соответствующую SQLAlchemy-колонку.
        # без sa_column SQLModel бы автоматически установил тип колонки DateTime(timezone=False)
        sa_column=Column( # класс SQLAlchemy, описывающий колонку в БД
            DateTime(timezone=True) # тип данных SQLAlchemy
        ),
        description="Время истечения срока действия токена"
    )