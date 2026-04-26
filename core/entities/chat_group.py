from enum import StrEnum
from pydantic import Field
from .base import Base


class ChatGroup(Base):
    class Type(StrEnum):
        SYSTEM = 'system'
        USER = 'user'

    title: str
    user_id: int
    chat_ids: list[int] = Field(default_factory=list)
    unread_messages_count: int = 0
    type: Type = Type.USER

    class Creation(Base.Creation):
        title: str
        user_id: int
        chat_ids: list[int] = Field(default_factory=list)
