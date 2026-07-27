from __future__ import annotations

from core.repos.message import AbstractMessageRepo, DbMessageRepo
from core.repos.room import AbstractRoomRepo
from db.misc.defaults import default_timestamp
from db.session import Session, SessionLocal


class RoomUoWFactory:
    def __init__(
        self,
        room_repo_class: type[AbstractRoomRepo],
        message_repo_class: type[AbstractMessageRepo] = DbMessageRepo,
    ):
        self.room_repo_class = room_repo_class
        self.message_repo_class = message_repo_class

    def __call__(self) -> RoomUnitOfWork:
        return RoomUnitOfWork(
            youtube_room_repo=self.room_repo_class(auto_commit=False),
            message_repo=self.message_repo_class(auto_commit=False),
        )


class RoomUnitOfWork:
    def __init__(
        self,
        youtube_room_repo: AbstractRoomRepo,
        message_repo: AbstractMessageRepo,
    ):
        self.youtube_room_repo = youtube_room_repo
        self.message_repo = message_repo
        self._session: Session | None = None

    def current_time(self) -> float:
        return default_timestamp()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def __enter__(self) -> RoomUnitOfWork:
        self._session = SessionLocal()
        self.youtube_room_repo._session = self._session
        self.message_repo._session = self._session
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._session.close()
