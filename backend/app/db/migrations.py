from sqlalchemy import text

from .base import make_engine
from .models import Base


def check_database() -> bool:
    with make_engine().connect() as connection:
        connection.execute(text('SELECT 1'))
        value = connection.execute(text("SELECT count(*) FROM pg_extension WHERE extname = 'postgis'")).scalar_one()
        return value == 1

def initialize_database() -> None:
    engine = make_engine()
    with engine.begin() as connection:
        connection.execute(text('CREATE EXTENSION IF NOT EXISTS postgis'))
    Base.metadata.create_all(engine)
