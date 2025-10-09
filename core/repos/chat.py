from abc import ABC, abstractmethod
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from db.models import Chat as ChatModel, Participant as ParticipantModel
from db.session import session_factory, Session

from core.entities.chat import Chat, ChatType
from .base import InMemoryRepo, DbRepo
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


class DbChatRepo(DbRepo, AbstractChatRepo):
    model = ChatModel
    participant_model = ParticipantModel
    entity_model = Chat

    @session_factory
    def find_one(self, user_id: int | None = None, type: ChatType | None = None, *, session: Session) -> Chat | None:
        ...

    @session_factory
    def find_all_by_user_id(self, user_id: int, *, session: Session) -> list[Chat]:
        query = (
            select(self.model)
            .join(self.participant_model)
            .where(self.participant_model.user_id == user_id)
            .options(joinedload(self.model.participants))
        )
        chats = session.execute(query).unique().scalars().all()
        return [Chat.model_validate(chat, from_attributes=True) for chat in chats]


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
