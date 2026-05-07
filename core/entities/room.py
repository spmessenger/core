from .base import Base


class YouTubeRoomModel(Base):
    id: int
    chat_id: int
    message_id: int

    class Creation(Base.Creation):
        id: int
        chat_id: int
        message_id: int
