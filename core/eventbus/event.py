from enum import StrEnum


class EventType(StrEnum):
    MESSAGE_CREATED = 'message.created'
    CHAT_UPDATE = 'chat.update'
