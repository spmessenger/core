from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    SECRET_KEY: str = 'secret'


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
