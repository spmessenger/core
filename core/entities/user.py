from typing import NewType
from .base import Base


UserId = NewType("UserId", int)


class User(Base):
    id: UserId
    username: str
    hashed_password: str

    class Creation(Base.Creation):
        username: str
        hashed_password: str
