from .base import Base


class Reply(Base):
    id: int
    replying_msg_id: int
    reply_to_msg_id: int

    class Creation(Base.Creation):
        replying_msg_id: int
        reply_to_msg_id: int
