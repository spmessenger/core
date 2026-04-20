from abc import ABC, abstractmethod
from sqlalchemy import asc, select
from core.entities.message import Message
from db.models import Message as ModelMessage
from db.session import session_factory, Session
from .base import InMemoryRepo, DbRepo


class AbstractMessageRepo(ABC):
    @abstractmethod
    def get_one(self, id: int) -> Message:
        pass

    @abstractmethod
    def find_one(self, id: int) -> Message | None:
        pass

    @abstractmethod
    def find_all(self, chat_id: int | None = None) -> list[Message]:
        pass

    @abstractmethod
    def save(self, message: Message.Creation) -> Message:
        pass

    @abstractmethod
    def find_page(
        self,
        chat_id: int,
        before_message_id: int | None = None,
        limit: int = 50,
    ) -> tuple[list[Message], bool]:
        pass


class DbMessageRepo(DbRepo, AbstractMessageRepo):
    model = ModelMessage
    entity_model = Message

    @session_factory
    def get_one(self, id: int, *, session: Session) -> Message:
        query = select(self.model).where(self.model.id == id)
        message = session.execute(query).scalar_one_or_none()
        if message is None:
            raise ValueError(f'Message with id={id} not found')
        return Message.model_validate(message, from_attributes=True)

    @session_factory
    def find_one(self, id: int, *, session: Session) -> Message | None:
        query = select(self.model).where(self.model.id == id)
        message = session.execute(query).scalar_one_or_none()
        if message is None:
            return None
        return Message.model_validate(message, from_attributes=True)

    @session_factory
    def find_all(self, chat_id: int | None = None, *, session: Session) -> list[Message]:
        query = select(self.model).order_by(asc(self.model.created_at_timestamp))

        if chat_id is not None:
            query = query.where(self.model.chat_id == chat_id)

        messages = session.execute(query).scalars().all()
        return [Message.model_validate(message, from_attributes=True) for message in messages]

    @session_factory
    def save(self, message: Message.Creation, *, session: Session) -> Message:
        return super().save(message, session=session)

    @session_factory
    def find_page(
        self,
        chat_id: int,
        before_message_id: int | None = None,
        limit: int = 50,
        *,
        session: Session,
    ) -> tuple[list[Message], bool]:
        query = (
            select(self.model)
            .where(self.model.chat_id == chat_id)
            .order_by(self.model.id.desc())
        )
        if before_message_id is not None:
            query = query.where(self.model.id < before_message_id)

        rows = session.execute(query.limit(limit + 1)).scalars().all()
        has_more = len(rows) > limit
        rows = rows[:limit]
        rows.reverse()
        return [Message.model_validate(message, from_attributes=True) for message in rows], has_more


class InMemoryMessageRepo(AbstractMessageRepo, InMemoryRepo[Message]):
    def get_one(self, id: int) -> Message:
        message = self.find_one(id=id)
        if message is None:
            raise ValueError(f'Message with id={id} not found')
        return message

    def find_one(self, id: int) -> Message | None:
        for message in self._storage:
            if message.id == id:
                return message
        return None

    def find_all(self, chat_id: int | None = None) -> list[Message]:
        if chat_id is None:
            return list(self._storage)
        return [message for message in self._storage if message.chat_id == chat_id]

    def save(self, message: Message.Creation) -> Message:
        entity = Message(
            id=0,
            chat_id=message.chat_id,
            content=message.content,
            participant_id=message.participant_id,
            reference_message_id=message.reference_message_id,
        )
        return self._save(entity)

    def find_page(
        self,
        chat_id: int,
        before_message_id: int | None = None,
        limit: int = 50,
    ) -> tuple[list[Message], bool]:
        messages = [message for message in self._storage if message.chat_id == chat_id]
        messages.sort(key=lambda message: message.id)

        if before_message_id is not None:
            messages = [message for message in messages if message.id < before_message_id]

        page = messages[-limit:]
        has_more = len(messages) > len(page)
        return page, has_more
