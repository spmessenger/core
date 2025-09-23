from typing import NewType
from .base import Base


UserId = NewType("UserId", int)


class User(Base):
    id: UserId
    name: str
    phone: str

    class Creation(Base.Creation):
        name: str
        phone: str
