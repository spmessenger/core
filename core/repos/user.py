from abc import ABC, abstractmethod
from core.entities.user import User


class AbstractUserRepo(ABC):
    @abstractmethod
    def save(self, user: User.Creation) -> User:
        pass


class InMemoryUserRepo(AbstractUserRepo):
    _storage: list[User] = []
    _last_id: int = 0

    def save(self, user: User.Creation) -> User:
        self._last_id += 1
        entity = User(
            id=self._last_id,
            username=user.username,
            hashed_password=user.hashed_password,
        )
        self._storage.append(entity)
        return entity
