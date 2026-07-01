from sqlmodel import Session, SQLModel, select, delete, create_engine
from models import UserInDB, RefreshToken
from datetime import timezone
from config import settings

engine = create_engine(settings.DATABASE_URL)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_user(session: Session, username: str) -> UserInDB | None:
    query = select(UserInDB).where(UserInDB.username == username)
    user = session.exec(query).first()
    return user

def add_user(session: Session, user: UserInDB) -> None:
    session.add(user)
    session.commit()





def get_refresh_token(session: Session, refresh_token: str) -> RefreshToken | None:
    query = select(RefreshToken).where(RefreshToken.token == refresh_token)
    data = session.exec(query).first()
    if data and data.expires_at.tzinfo is None:
        data.expires_at = data.expires_at.replace(tzinfo=timezone.utc)
    return data


def add_refresh_token(session: Session, refresh_token: RefreshToken):
    session.add(refresh_token)
    session.commit()

def delete_refresh_token(session: Session, refresh_token: str | RefreshToken):
    if isinstance(refresh_token, RefreshToken):
        refresh_token = refresh_token.token
    
    query = delete(RefreshToken).where(RefreshToken.token == refresh_token)
    session.exec(query)
    session.commit()

def set_refresh_token_expire_date(session: Session, refresh_token: RefreshToken):
    session.add(refresh_token)
    session.commit()






def enforce_session_limit(session: Session, username):
    query = select(RefreshToken).where(RefreshToken.username == username).order_by(RefreshToken.expires_at)
    res = session.exec(query).all()
    if len(res) >= settings.MAX_SESSIONS_PER_USER:
        oldest = res[0]
        query = delete(RefreshToken).where(RefreshToken.id == oldest.id)
        session.exec(query)
        session.commit()