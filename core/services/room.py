from uuid import uuid4

from core.entities.room import RoomType, YouTubeRoom
from core.uow.room import RoomUoWFactory


class BaseRoomService:
    def join(self, room_id: str):
        raise NotImplementedError()

    def leave(self, room_id: str):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def gen_room_id(self):
        return uuid4().hex


class YouTubeRoomService(BaseRoomService):
    def __init__(self, uow_factory: RoomUoWFactory):
        self.uow_factory = uow_factory

    def create(self, youtube_video_id: str, user_id: int | None = None, message_id: int | None = None):
        with self.uow_factory() as uow:
            room = uow.youtube_room_repo.save(
                YouTubeRoom.Creation(
                    type=RoomType.YOUTUBE.value,
                    type_specific_metadata=YouTubeRoom.SpecificMetadata(
                        youtube_video_id=youtube_video_id,
                    ).model_dump(),
                    created_at=uow.current_time(),
                )
            )
            if message_id:
                uow.message_repo.assign_youtube_room(message_id, room.id)
            uow.commit()
        return room
