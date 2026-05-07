from abc import ABC, abstractmethod
from sqlalchemy import select

from core.entities.room import YouTubeRoomModel
from db.models import YouTubeRoom as YouTubeRoomDbModel
from db.session import session_factory, Session
from .base import InMemoryRepo, DbRepo


class AbstractYouTubeRoomRepo(ABC):
    @abstractmethod
    def find_by_id(self, room_id: int) -> YouTubeRoomModel | None:
        pass

    @abstractmethod
    def create(self, room: YouTubeRoomModel.Creation) -> YouTubeRoomModel:
        pass


class DbYouTubeRoomRepo(DbRepo, AbstractYouTubeRoomRepo):
    model = YouTubeRoomDbModel
    entity_model = YouTubeRoomModel

    @session_factory
    def find_by_id(self, room_id: int, *, session: Session) -> YouTubeRoomModel | None:
        query = (
            select(self.model)
            .where(self.model.id == room_id)
        )
        room = session.execute(query).scalar_one_or_none()
        if room is None:
            return None
        return YouTubeRoomModel.model_validate(room, from_attributes=True)

    @session_factory
    def create(self, room: YouTubeRoomModel.Creation, *, session: Session) -> YouTubeRoomModel:
        return super().save(room, session=session)


class InMemoryYouTubeRoomRepo(InMemoryRepo[YouTubeRoomModel], AbstractYouTubeRoomRepo):
    def find_by_id(self, room_id: int) -> YouTubeRoomModel | None:
        return self._find_by('id', room_id)

    def create(self, room: YouTubeRoomModel.Creation) -> YouTubeRoomModel:
        entity = YouTubeRoomModel(
            id=room.id,
            chat_id=room.chat_id,
            message_id=room.message_id,
        )
        self._storage.append(entity)
        return entity
