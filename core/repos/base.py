from typing import Any, Generic, TypeVar, Iterable
from sqlalchemy import delete, update

from core.entities.base import Base
from db.base import Base as DbBase
from db.session import asession_factory, session_factory, AsyncSession, Session

T = TypeVar("T", bound=Base)


class DbRepo(Generic[T]):
    model: DbBase
    entity_model: T

    @asession_factory
    async def adelete(self, id: int, *, session: AsyncSession) -> bool:
        db_model = await self._adelete(id, session)
        await session.commit()
        return await self.apost_delete(id, db_model)

    @asession_factory
    async def aupdate(self, obj: Base, consider_all: bool = False, *, session: AsyncSession) -> Base | None:
        db_model = await self._aupdate(obj=obj, consider_all=consider_all, session=session)
        await session.commit()
        return await self.apost_update(obj, db_model)

    @session_factory
    def update(self, obj: Base, consider_all: bool = False, *, session: Session) -> Base | None:
        db_model = self._update(obj=obj, consider_all=consider_all, session=session)
        session.commit()
        return self.post_update(obj, db_model)

    @asession_factory
    async def asave(self, obj: Base, *, session: AsyncSession) -> Base | None:
        db_model = await self._asave(obj, session)
        await session.commit()
        return await self.apost_save(obj, db_model)

    @session_factory
    def save(self, obj: Base, *, session: Session) -> Base | None:
        db_model = self._save(obj, session)
        session.commit()
        return self.post_save(obj, db_model)

    @asession_factory
    async def asave_many(self, objs: Iterable[Base], *, session: AsyncSession) -> list[Base]:
        await self._asave_many(objs, session)
        await session.commit()

    async def apost_save(self, obj: Base, db_model: DbBase):
        pass

    def post_save(self, obj: Base, db_model: DbBase):
        return self.entity_model.model_validate(db_model, from_attributes=True)

    async def apost_update(self, obj: Base, db_model):
        pass

    def post_update(self, obj: Base, db_model: DbBase):
        return self.entity_model.model_validate(db_model, from_attributes=True)

    async def apost_delete(self, id: int, db_model) -> bool:
        return db_model is not None

    async def _adelete(self, id: int, session: AsyncSession):
        query = (
            delete(self.model)
            .where(self.model.id == id)
            .returning(self.model)
        )
        db_model = await session.execute(query)
        await session.flush()
        return db_model.scalar_one()

    async def _asave_many(self, objs: Iterable[Base], session: AsyncSession) -> list[Base]:
        db_models = []
        for obj in objs:
            db_model = await self._asave(obj, session)
            db_models.append(db_model)
        return db_models

    async def _aupdate(self, obj: Base, consider_all: bool = False, session: AsyncSession | None = None):
        if obj.id is None:
            raise ValueError('id cannot be None')
        model_dump = self._get_update_model_dump(obj, consider_all)
        query = (
            update(self.model)
            .where(self.model.id == obj.id)
            .values(model_dump)
            .returning(self.model)
        )
        db_model = await session.execute(query)
        await session.flush()
        return db_model.unique().scalar_one()

    def _update(self, obj: Base, consider_all: bool = False, session: Session | None = None):
        if obj.id is None:
            raise ValueError('id cannot be None')
        model_dump = self._get_update_model_dump(obj, consider_all)
        query = (
            update(self.model)
            .where(self.model.id == obj.id)
            .values(model_dump)
            .returning(self.model)
        )
        db_model = session.execute(query).unique().scalar_one()
        return db_model

    async def _asave(self, obj: Base, session: AsyncSession):
        model_dump = self._get_model_dump(obj)
        db_model = self.model(**model_dump)
        session.add(db_model)
        await session.flush()
        try:
            obj.id = db_model.id
        except ValueError:
            pass  # TODO: need to log here
        return db_model

    def _save(self, obj: Base, session: Session):
        model_dump = self._get_model_dump(obj)
        db_model = self.model(**model_dump)
        session.add(db_model)
        try:
            obj.id = db_model.id
        except ValueError:
            pass  # TODO: need to log here
        return db_model

    def _get_update_model_dump(self, obj: Base, consider_all: bool = False) -> dict:
        return obj.model_dump(exclude={'id'}, exclude_unset=not consider_all)

    def _get_model_dump(self, obj: Base) -> dict:
        return obj.model_dump(exclude={'id'})


class InMemoryRepo(Generic[T]):
    _storage: list[T] = []
    _last_id: int = 0

    def _check(self, entity: T):
        for key, value in entity.__class__.model_fields.items():
            if value.json_schema_extra is None:
                continue

            if value.json_schema_extra.get("unique") is True:
                entity_val = getattr(entity, key)
                if self._find_by(key, entity_val) is not None:
                    raise ValueError(f"Field {key} is not unique")

    def _find_by(self, key: str, value: Any) -> T | None:
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

    def _update(self, upd_ent: Base.Update) -> T:  # todo: need to replace Base.Update with T.Update
        entity = self._find_by('id', upd_ent.id)
        if entity is None:
            raise ValueError(f"Entity with id {upd_ent.id} not found")
        for key, value in upd_ent.model_dump(exclude={'id'}, exclude_none=True).items():
            setattr(entity, key, value)
        return entity
