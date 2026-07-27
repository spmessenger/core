from __future__ import annotations
from typing import NewType
from pydantic import BaseModel, Field
from .base import Base


MessageId = NewType("MessageId", int)


class Message(Base):
    id: MessageId
    chat_id: int
    participant_id: int
    reference_message_id: int | None = None
    reference_author: str | None = None
    reference_content: str | None = None
    forwarded_from_message_id: int | None = None
    forwarded_from_author: str | None = None
    forwarded_from_author_avatar_url: str | None = None
    forwarded_from_content: str | None = None
    metadata_: dict = Field(default_factory=dict)
    content: str
    created_at_timestamp: float
    reply_to: ReplyTo | None = None

    class ReplyTo(BaseModel):
        participant_id: int
        id: MessageId
        content: str

    class Creation(Base.Creation):
        chat_id: int
        participant_id: int
        reference_message_id: int | None = None
        reference_author: str | None = None
        reference_content: str | None = None
        forwarded_from_message_id: int | None = None
        forwarded_from_author: str | None = None
        forwarded_from_author_avatar_url: str | None = None
        forwarded_from_content: str | None = None
        metadata_: dict = Field(default_factory=dict)
        content: str
