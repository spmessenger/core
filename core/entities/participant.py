from enum import StrEnum
from .base import Base


DEFAULT_PIN_POSITION = 0
PRIVATE_CHAT_PIN_POSITION = 1


class ParticipantType(StrEnum):
    ADMIN = 'admin'
    MEMBER = 'member'


class Participant(Base):
    id: int
    chat_id: int
    user_id: int
    role: ParticipantType
    draft: str | None = None
    pin_position: int = 0
    chat_visible: bool = True

    class Update(Base.Update):
        id: int
        pinned: bool | None = None
        draft: str | None = None
        pin_position: int | None = None
        chat_visible: bool | None = None

    class Creation(Base.Creation):
        chat_id: int
        user_id: int
        role: ParticipantType
        draft: str | None = None
        pin_position: int = 0
        chat_visible: bool = True

    class AdminCreation(Creation):
        role: ParticipantType = ParticipantType.ADMIN

    class MemberCreation(Creation):
        role: ParticipantType = ParticipantType.MEMBER
