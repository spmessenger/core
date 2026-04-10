from pydantic import Field
from .base import Base


class ChatGroup(Base):
    title: str
    user_id: int
    chat_ids: list[int] = Field(default_factory=list)

    class Creation(Base.Creation):
        title: str
        user_id: int
        chat_ids: list[int] = Field(default_factory=list)
