from abc import ABC, abstractmethod
from core.entities.chat import Chat, ChatType
from .base import InMemoryRepo
from .participant import InMemoryParticipantRepo


class AbstractChatRepo(ABC):
    @abstractmethod
    def find_one(self, user_id: int | None = None, type: ChatType | None = None) -> Chat | None:
        pass

    @abstractmethod
    def find_all_by_user_id(self, user_id: int) -> list[Chat]:
        pass

    @abstractmethod
    def save(self, chat: Chat.Creation) -> Chat:
        pass


class InMemoryChatRepo(AbstractChatRepo, InMemoryRepo[Chat]):
    def __init__(self):
        super().__init__()
        self._participant_repo = InMemoryParticipantRepo()  # TODO: need to inject, not to create new instance

    def find_all_by_user_id(self, user_id: int) -> list[Chat]:
        chat_ids = {participant.chat_id for participant in self._participant_repo.find_all_by_user_id(user_id)}
        return [ent for ent in self._storage if ent.id in chat_ids]

    def save(self, chat: Chat.Creation) -> Chat:
        entity = Chat(
            id=0,
            title=chat.title,
            type=chat.type,
        )
        return self._save(entity)
