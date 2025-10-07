from abc import ABC, abstractmethod
from core.entities.user import User
from .base import InMemoryRepo


class AbstractUserRepo(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> User:
        pass

    @abstractmethod
    def find_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    def find_by_username(self, username: str) -> User | None:
        pass

    @abstractmethod
    def save(self, user: User.Creation) -> User:
        pass

    @abstractmethod
    def update(self, user: User.Update) -> User:
        pass


class InMemoryUserRepo(InMemoryRepo[User], AbstractUserRepo):
    _storage: list[User] = []
    _last_id: int = 0

    def get_by_id(self, user_id: int) -> User:
        for user in self._storage:
            if user.id == user_id:
                return user
        raise ValueError(f'User with id {user_id} not found')

    def find_by_id(self, user_id: int) -> User | None:
        for user in self._storage:
            if user.id == user_id:
                return user
        return None

    def find_by_username(self, username: str) -> User | None:
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
