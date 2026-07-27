from abc import ABC, abstractmethod
from sqlalchemy import select

from core.entities.room import Room
from db.models import Room as RoomModel
from db.session import session_factory, Session
from .base import DbRepo, InMemoryRepo


class AbstractRoomRepo(ABC):
    @abstractmethod
    def find_by_id(self, room_id: int) -> Room | None:
        pass

    @abstractmethod
    def save(self, room: Room.Creation) -> Room:
        pass


class DbRoomRepo(DbRepo, AbstractRoomRepo):
    model = RoomModel
    entity_model = Room

    @session_factory
    def find_by_id(self, room_id: int, *, session: Session) -> Room | None:
        query = select(self.model).where(self.model.id == room_id)
        room = session.execute(query).scalar_one_or_none()
        if room is None:
            return None
        return Room.model_validate(room, from_attributes=True)


class InMemoryRoomRepo(InMemoryRepo[Room], AbstractRoomRepo):
    def find_by_id(self, room_id: int) -> Room | None:
        return self._find_by('id', room_id)

    def save(self, room: Room.Creation) -> Room:
        entity = Room(
            id=0,
            type=room.type,
            type_specific_metadata=room.type_specific_metadata,
            created_at=room.created_at,
        )
        return self._save(entity)


AbstractYouTubeRoomRepo = AbstractRoomRepo
DbYouTubeRoomRepo = DbRoomRepo
InMemoryYouTubeRoomRepo = InMemoryRoomRepo
