from typing import Generic, TypeVar

T = TypeVar("T")


class InMemoryRepo(Generic[T]):
    _storage: list[T] = []
    _last_id: int = 0

    def _check(self, entity: T) -> T:
        for key, value in entity.__class__.model_fields.items():
            if value.json_schema_extra is None:
                continue

            if value.json_schema_extra.get("unique") is True:
                entity_val = getattr(entity, key)
                if self._find_by(key, entity_val) is not None:
                    raise ValueError(f"Field {key} is not unique")

    def _find_by(self, key: str, value: str) -> T | None:
        for entity in self._storage:
            if getattr(entity, key) == value:
                return entity
        return None

    def _save(self, entity: T) -> T:
        self._check(entity)
        self._last_id += 1
        entity.id = self._last_id
        self._storage.append(entity)
        return entity
