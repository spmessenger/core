from abc import ABC, abstractmethod
from core.entities.message import Message
from db.models import Message as ModelMessage
from db.session import session_factory, Session
from .base import InMemoryRepo, DbRepo


class AbstractMessageRepo(ABC):
    @abstractmethod
    def save(self, message: Message.Creation) -> Message:
        pass


class DbMessageRepo(DbRepo, AbstractMessageRepo):
    model = ModelMessage
    entity_model = Message

    @session_factory
    def save(self, message: Message.Creation, *, session: Session) -> Message:
        return super().save(message, session=session)


class InMemoryMessageRepo(AbstractMessageRepo, InMemoryRepo[Message]):
    def save(self, message: Message.Creation) -> Message:
        entity = Message(
            id=0,
            chat_id=message.chat_id,
            content=message.content,
            participant_id=message.participant_id,
        )
        return self._save(entity)
