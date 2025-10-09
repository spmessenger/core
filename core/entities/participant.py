from .base import Base


class Participant(Base):
    id: int
    chat_id: int
    user_id: int

    class Creation(Base.Creation):
        chat_id: int
        user_id: int
