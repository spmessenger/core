from abc import ABC, abstractmethod
from core.entities.chat import Chat
from .base import InMemoryRepo


class AbstractChatRepo(ABC):
    @abstractmethod
    def save(self, chat: Chat.Creation) -> Chat:
        pass


class InMemoryChatRepo(AbstractChatRepo, InMemoryRepo[Chat]):
    def save(self, chat: Chat.Creation) -> Chat:
        entity = Chat(
            id=0,
            title=chat.title,
            type=chat.type,
        )
        return self._save(entity)