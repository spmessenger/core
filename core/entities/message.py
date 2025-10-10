from typing import NewType
from .base import Base


MessageId = NewType("MessageId", int)


class Message(Base):
    id: MessageId
    chat_id: int
    participant_id: int
    content: str
    created_at_timestamp: float

    class Creation(Base.Creation):
        chat_id: int
        participant_id: int
        content: str
