from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    demo_synthetic: bool = True
    database_url: str = 'postgresql+psycopg://civisar:civisar_local_only@localhost:5432/civisar'
    allowed_origin: str = 'http://localhost:5173'
    cookie_secure: bool = False
    civisar_demo_users_json: str = '{}'
    # Root of the private/local data folders (relative to the repository root unless absolute).
    data_root: str = 'data'

@lru_cache
def get_settings() -> Settings:
    return Settings()
