from abc import ABC, abstractmethod
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from db.models import Chat as ChatModel, Participant as ParticipantModel
from db.session import session_factory, Session
from db.misc.cond import cond_seq

from core.entities.chat import Chat, ChatType
from .base import InMemoryRepo, DbRepo
from .participant import InMemoryParticipantRepo


class AbstractChatRepo(ABC):
    @abstractmethod
    def get_by_id(self, chat_id: int) -> Chat:
        pass

    @abstractmethod
    def find_private_chat(self, user_id: int) -> Chat | None:
        pass

    @abstractmethod
    def find_all(self, user_id: int | None = None, type: ChatType | None = None) -> Chat | None:
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
    def find_private_chat(self, user_id: int, *, session: Session) -> Chat | None:
        query = (
            select(self.model)
            .join(self.participant_model)
            .where(self.model.type == ChatType.PRIVATE)
            .where(self.participant_model.user_id == user_id)
            .limit(1)
        )
        chat = session.execute(query).scalar_one_or_none()
        if chat is None:
            return None
        return Chat.model_validate(chat, from_attributes=True)

    @session_factory
    def get_by_id(self, chat_id: int, *, session: Session) -> Chat:
        query = (
            select(self.model)
            .where(self.model.id == chat_id)
            .limit(1)
        )
        chat = session.execute(query).scalar_one_or_none()
        if chat is None:
            raise ValueError(f'Chat with id {chat_id} not found')
        return Chat.model_validate(chat, from_attributes=True)

    @session_factory
    def find_all(self, user_id: int | None = None, type: ChatType | None = None, *, session: Session) -> list[Chat]:
        conds = (
            cond_seq()
            .and_(self.model.type == type)
            .and_(self.participant_model.user_id == user_id)
        )
        query = (
            select(self.model)
            .join(self.participant_model)
            .where(*conds.clauses)
            .options(joinedload(self.model.participants))
        )
        chat = session.execute(query).unique().scalars().all()
        return [Chat.model_validate(chat, from_attributes=True) for chat in chat]

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
