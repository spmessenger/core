from typing import NewType
from pydantic import Field
from .base import Base


UserId = NewType("UserId", int)


class User(Base):
    id: UserId
    username: str = Field(json_schema_extra={'unique': True})
    hashed_password: str
    refresh_tokens: list[str] = Field(default_factory=list)

    class Creation(Base.Creation):
        username: str
        hashed_password: str

    class Update(Base.Update):
        id: int
        username: str | None = None
        hashed_password: str | None = None
        refresh_tokens: list[str] | None
