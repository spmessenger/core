import enum
from pydantic import BaseModel

from .base import Base


class RoomType(enum.Enum):
    YOUTUBE = 'youtube'


class Room(Base):
    id: int
    type: str
    type_specific_metadata: dict
    created_at: float

    class Creation(Base.Creation):
        type: str
        type_specific_metadata: dict
        created_at: float


class YouTubeRoom(Room):
    class SpecificMetadata(BaseModel):
        youtube_video_id: str

    type: str = RoomType.YOUTUBE.value
    type_specific_metadata: SpecificMetadata
