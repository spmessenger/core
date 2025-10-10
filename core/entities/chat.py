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

    class Creation(Base.Creation):
        type: ChatType
        title: str | None = None

    class DialogCreation(Creation):
        type: ChatType = ChatType.DIALOG

    class GroupChatCreation(Creation):
        type: ChatType = ChatType.GROUP

    class PrivateChatCreation(Creation):
        type: ChatType = ChatType.PRIVATE
