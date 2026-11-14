from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from .base import make_engine


def check_database() -> bool:
    with make_engine().connect() as connection:
        connection.execute(text('SELECT 1'))
        value = connection.execute(text("SELECT count(*) FROM pg_extension WHERE extname = 'postgis'")).scalar_one()
        return value == 1

def initialize_database() -> None:
    root = Path(__file__).resolve().parents[3]
    command.upgrade(Config(str(root / 'backend/alembic.ini')), 'head')
