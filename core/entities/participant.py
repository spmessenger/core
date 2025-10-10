from enum import StrEnum
from .base import Base


class ParticipantType(StrEnum):
    ADMIN = 'admin'
    MEMBER = 'member'


class Participant(Base):
    id: int
    chat_id: int
    user_id: int
    role: ParticipantType
    draft: str | None = None
    pinned: bool = False

    class Update(Base.Update):
        id: int
        pinned: bool | None = None
        draft: str | None = None

    class Creation(Base.Creation):
        chat_id: int
        user_id: int
        role: ParticipantType

    class AdminCreation(Creation):
        role: ParticipantType = ParticipantType.ADMIN

    class MemberCreation(Creation):
        role: ParticipantType = ParticipantType.MEMBER
