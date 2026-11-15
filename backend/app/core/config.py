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
    # Team decision 15 Nov 2026: the dashboard has no sign-in. With real data (DEMO_SYNTHETIC=false)
    # and this on, anonymous GET requests read every real-data route as a read-only coordinator over
    # the whole demo box. Writes (reviews, briefs, admin) still need a signed-in session.
    public_real_data: bool = False
    # Seconds the /map/context bundle is cached (it takes 15-20 s to build).
    map_context_cache_s: int = 300

@lru_cache
def get_settings() -> Settings:
    return Settings()
