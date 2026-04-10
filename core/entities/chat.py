from enum import StrEnum
from pydantic import Field
from .base import Base


class ChatType(StrEnum):
    DIALOG = 'dialog'
    GROUP = 'group'
    PRIVATE = 'private'


class Chat(Base):
    id: int
    type: ChatType
    title: str | None = None
    avatar_url: str | None = None
    last_message: str | None = None
    last_message_at: str | None = None
    unread_messages_count: int = 0
    pin_position: int = 0

    class Creation(Base.Creation):
        type: ChatType
        title: str | None = None
        avatar_url: str | None = None

    class DialogCreation(Creation):
        type: ChatType = ChatType.DIALOG

    class GroupChatCreation(Creation):
        type: ChatType = ChatType.GROUP

    class PrivateChatCreation(Creation):
        type: ChatType = ChatType.PRIVATE
