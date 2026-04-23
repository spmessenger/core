from abc import ABC, abstractmethod
from sqlalchemy import asc, delete, select, update
from core.entities.message import Message
from db.models import Message as ModelMessage, chat_last_message_association_table
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
    def delete_one(self, id: int) -> Message:
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
    chat_last_message_association_model = chat_last_message_association_table
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
    def delete_one(self, id: int, *, session: Session) -> Message:
        # Clear message references in other messages before deleting the target row.
        session.execute(
            update(self.model)
            .where(self.model.reference_message_id == id)
            .values(reference_message_id=None)
        )
        session.execute(
            update(self.model)
            .where(self.model.forwarded_from_message_id == id)
            .values(forwarded_from_message_id=None)
        )
        # Clear chat "last message" association if it points to the deleted message.
        session.execute(
            delete(self.chat_last_message_association_model)
            .where(self.chat_last_message_association_model.c.message_id == id)
        )
        query = (
            delete(self.model)
            .where(self.model.id == id)
            .returning(self.model)
        )
        deleted_model = session.execute(query).scalar_one_or_none()
        if deleted_model is None:
            raise ValueError(f'Message with id={id} not found')
        session.commit()
        return Message.model_validate(deleted_model, from_attributes=True)

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
            reference_author=message.reference_author,
            reference_content=message.reference_content,
            forwarded_from_message_id=message.forwarded_from_message_id,
            forwarded_from_author=message.forwarded_from_author,
            forwarded_from_author_avatar_url=message.forwarded_from_author_avatar_url,
            forwarded_from_content=message.forwarded_from_content,
        )
        return self._save(entity)

    def delete_one(self, id: int) -> Message:
        for message in self._storage:
            if message.reference_message_id == id:
                message.reference_message_id = None
            if message.forwarded_from_message_id == id:
                message.forwarded_from_message_id = None
        for index, message in enumerate(self._storage):
            if message.id == id:
                deleted_message = self._storage.pop(index)
                return deleted_message
        raise ValueError(f'Message with id={id} not found')

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
