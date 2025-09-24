from enum import StrEnum
from .base import Base



class ChatType(StrEnum):
    GROUP = 'group'
    PRIVATE = 'private'

class Chat(Base):
    id: int
    type: ChatType
    title: str | None = None

    class Creation(Base.Creation):
        type: ChatType
        title: str | None = None