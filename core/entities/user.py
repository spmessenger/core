from typing import NewType
from pydantic import Field
from .base import Base


UserId = NewType("UserId", int)


class User(Base):
    id: UserId
    username: str = Field(json_schema_extra={'unique': True})
    hashed_password: str

    class Creation(Base.Creation):
        username: str
        hashed_password: str
