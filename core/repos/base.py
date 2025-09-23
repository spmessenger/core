from typing import Generic, TypeVar

T = TypeVar("T")


class InMemoryRepo(Generic[T]):
    _storage: list[T] = []
    _last_id: int = 0

    def _save(self, entity: T) -> T:
        self._last_id += 1
        entity.id = self._last_id
        self._storage.append(entity)
        return entity
