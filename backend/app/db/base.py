from backend.app.core.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass

def make_engine():
    return create_engine(get_settings().database_url, pool_pre_ping=True,
                         connect_args={'connect_timeout': 3})

def make_session_factory():
    return sessionmaker(bind=make_engine())
