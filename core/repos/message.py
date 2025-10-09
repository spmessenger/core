from abc import ABC, abstractmethod
from core.entities.message import Message
from db.models import Message as ModelMessage
from .base import InMemoryRepo


class AbstractMessageRepo(ABC):
    @abstractmethod
    def save(self, message: Message.Creation) -> Message:
        pass


class DbMessageRepo():
    model = ModelMessage

    def save(self, message: Message.Creation) -> Message:
        ...


class InMemoryMessageRepo(AbstractMessageRepo, InMemoryRepo[Message]):
    def save(self, message: Message.Creation) -> Message:
        entity = Message(
            id=0,
            chat_id=message.chat_id,
            content=message.content,
            participant_id=message.participant_id,
        )
        return self._save(entity)
