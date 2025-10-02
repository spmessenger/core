from abc import ABC, abstractmethod
from core.entities.user import User


class AbstractUserRepo(ABC):
    @abstractmethod
    def find_by_username(self, username: str) -> User | None:
        pass

    @abstractmethod
    def save(self, user: User.Creation) -> User:
        pass


class InMemoryUserRepo(AbstractUserRepo):
    _storage: list[User] = []
    _last_id: int = 0

    def find_by_username(self, username: str) -> User | None:
        for user in self._storage:
            if user.username == username:
                return user
        return None

    def save(self, user: User.Creation) -> User:
        self._last_id += 1
        entity = User(
            id=self._last_id,
            username=user.username,
            hashed_password=user.hashed_password,
        )
        self._storage.append(entity)
        return entity
