from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    SECRET_KEY: str = 'secret'
    AUTH_DEFAULT_VERIFICATION_CODE: str = '0000'
    REDIS_URL: str = 'redis://localhost:6379/0'


@lru_cache()
def get_settings():
    return Settings()
