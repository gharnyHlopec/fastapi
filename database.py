from sqlmodel import select, delete, asc, desc
from models import UserInDB, RefreshToken
from datetime import timezone
from config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
import logging 

engine = create_async_engine(settings.DATABASE_URL)
logger = logging.getLogger("app")

async def get_user(session: AsyncSession, username: str) -> UserInDB | None:
    try:
        query = select(UserInDB).where(UserInDB.username == username)
        result = await session.execute(query)
        user = result.scalars().first()
        return user
    except Exception:
        logger.exception("Something went wrong while trying to get user from database")
        raise

async def get_particular_user(
    session: AsyncSession, 
    id: int
) -> UserInDB | None:
    try:
        query = select(UserInDB).where(UserInDB.id == id)
        result = await session.execute(query)
        user = result.scalars().first()
        return user
    except Exception:
        logger.exception("Something went wrong while trying to get particular user from database")
        raise

async def get_sorted_users(
    session: AsyncSession,
    username_substring: str | None,
    sort_by: str,
    sort_order: str
) -> list[UserInDB]:
    try:
        query = select(UserInDB)
        if username_substring:
            query = query.where(UserInDB.username.icontains(username_substring))
        
        sort_column = UserInDB.username if sort_by == "username" else UserInDB.created_at
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        return list(users)
    except Exception:
        logger.exception("Something went wrong while trying to get sorted users from database")
        raise

async def add_user(session: AsyncSession, user: UserInDB) -> None:
    try:
        session.add(user)
        await session.commit()
    except Exception:
        logger.exception("Something went wrong while trying to add user to database")
        raise
    



async def get_refresh_token(session: AsyncSession, refresh_token: str) -> RefreshToken | None:
    try:
        query = select(RefreshToken).where(RefreshToken.token == refresh_token)
        result = await session.execute(query)
        data = result.scalars().first()
        if data and data.expires_at.tzinfo is None:
            data.expires_at = data.expires_at.replace(tzinfo=timezone.utc)
        return data
    except Exception:
        logger.exception("Something went wrong while trying to get refresh token from database")
        raise


async def add_refresh_token(session: AsyncSession, refresh_token: RefreshToken):
    try:
        session.add(refresh_token)
        await session.commit()
    except Exception:
        logger.exception("Something went wrong while trying to add refresh token to database")
        raise

async def delete_refresh_token(session: AsyncSession, refresh_token: str | RefreshToken):
    try:
        if isinstance(refresh_token, RefreshToken):
            refresh_token = refresh_token.token
        
        query = delete(RefreshToken).where(RefreshToken.token == refresh_token)
        await session.execute(query)
        await session.commit()
    except Exception:
        logger.exception("Something went wrong while trying to delete refresh token from database")
        raise

async def set_refresh_token_expire_date(session: AsyncSession, refresh_token: RefreshToken):
    try:
        session.add(refresh_token)
        await session.commit()
    except Exception:
        logger.exception("Something went wrong while trying to set refresh token expire date")
        raise





async def enforce_session_limit(session: AsyncSession, username: str):
    try:
        query = select(RefreshToken).where(RefreshToken.username == username).order_by(RefreshToken.expires_at)
        result = await session.execute(query)
        sessions = result.scalars().all()
        if len(sessions) >= settings.MAX_SESSIONS_PER_USER:
            oldest = sessions[0]
            query = delete(RefreshToken).where(RefreshToken.id == oldest.id)
            await session.execute(query)
            await session.commit()
    except Exception:
        logger.exception("Something went wrong while trying to enforce session limit")
        raise