from typing import NewType
from pydantic import Field
from .base import Base


UserId = NewType("UserId", int)


class User(Base):
    id: UserId
    username: str = Field(json_schema_extra={'unique': True})
    email: str = Field(json_schema_extra={'unique': True})
    hashed_password: str
    refresh_tokens: list[str] = Field(default_factory=list)
    avatar_url: str | None = None
    subscription_tier: str = 'free'
    youtube_assisted_enabled: bool = False

    class Creation(Base.Creation):
        username: str
        email: str
        hashed_password: str
        avatar_url: str | None = None
        subscription_tier: str = 'free'
        youtube_assisted_enabled: bool = False

    class Update(Base.Update):
        id: int
        username: str | None = None
        email: str | None = None
        hashed_password: str | None = None
        refresh_tokens: list[str] | None = None
        avatar_url: str | None = None
        subscription_tier: str | None = None
        youtube_assisted_enabled: bool | None = None
