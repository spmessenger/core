from abc import ABC, abstractmethod
from sqlalchemy import select

from core.entities.user import User
from db.models import User as UserModel
from db.session import session_factory, Session
from .base import InMemoryRepo, DbRepo


class AbstractUserRepo(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> User:
        pass

    @abstractmethod
    def find_one_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    def find_one_by_username(self, username: str) -> User | None:
        pass

    @abstractmethod
    def save(self, user: User.Creation) -> User:
        pass

    @abstractmethod
    def update(self, user: User.Update) -> User:
        pass


class DbUserRepo(DbRepo, AbstractUserRepo):
    model = UserModel
    entity_model = User

    @session_factory
    def get_by_id(self, user_id: int, *, session: Session) -> User:
        query = (
            select(self.model)
            .where(self.model.id == user_id)
            .limit(1)
        )
        user = session.execute(query).scalar_one()
        if user is None:
            raise ValueError(f'User with id {user_id} not found')
        return User.model_validate(user, from_attributes=True)

    @session_factory
    def find_one_by_id(self, user_id: int, *, session: Session) -> User | None:
        query = (
            select(self.model)
            .where(self.model.id == user_id)
            .limit(1)
        )
        user = session.execute(query).scalar_one()
        if user is None:
            return None
        return User.model_validate(user, from_attributes=True)

    @session_factory
    def find_one_by_username(self, username: str, *, session: Session) -> User | None:
        query = (
            select(self.model)
            .where(self.model.username == username)
            .limit(1)
        )
        user = session.execute(query).scalar_one()
        if user is None:
            return None
        return User.model_validate(user, from_attributes=True)

    @session_factory
    def save(self, user: User.Creation, *, session: Session) -> User:
        return super().save(user, session=session)

    @session_factory
    def update(self, upd: User.Update, *, session: Session) -> User:
        return super().update(upd, session=session)


class InMemoryUserRepo(InMemoryRepo[User], AbstractUserRepo):
    _storage: list[User] = []
    _last_id: int = 0

    def get_by_id(self, user_id: int) -> User:
        for user in self._storage:
            if user.id == user_id:
                return user
        raise ValueError(f'User with id {user_id} not found')

    def find_one_by_id(self, user_id: int) -> User | None:
        for user in self._storage:
            if user.id == user_id:
                return user
        return None

    def find_one_by_username(self, username: str) -> User | None:
        for user in self._storage:
            if user.username == username:
                return user
        return None

    def update(self, upd: User.Update) -> User:
        updted_entity = self._update(upd)
        return User.model_validate(updted_entity, from_attributes=True)

    def save(self, user: User.Creation) -> User:
        entity = User(
            id=self._last_id,
            username=user.username,
            hashed_password=user.hashed_password,
        )
        return self._save(entity)
