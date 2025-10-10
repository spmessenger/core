from abc import ABC, abstractmethod
from sqlalchemy import asc, desc, insert, select, update
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy.dialects.postgresql import insert as pg_insert
from db.models import Chat as ChatModel, Participant as ParticipantModel, Message as MessageModel, chat_last_message_association_table
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
    def find_all(self, user_id: int | None = None, type: ChatType | None = None) -> list[Chat]:
        pass

    @abstractmethod
    def find_all_by_user_id(self, user_id: int) -> list[Chat]:
        pass

    @abstractmethod
    def update_last_message(self, chat_id: int, message_id: int):
        pass

    @abstractmethod
    def save(self, chat: Chat.Creation) -> Chat:
        pass


class DbChatRepo(DbRepo, AbstractChatRepo):
    model = ChatModel
    messages_model = MessageModel
    participant_model = ParticipantModel
    ass_model = chat_last_message_association_table
    entity_model = Chat

    @session_factory
    def find_private_chat(self, user_id: int, *, session: Session) -> Chat | None:
        query = (
            select(self.model)
            .join(self.participant_model)
            .where(self.model.type == ChatType.PRIVATE)
            .where(self.participant_model.user_id == user_id)
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
        )
        chat = session.execute(query).scalar_one_or_none()
        if chat is None:
            raise ValueError(f'Chat with id {chat_id} not found')
        return Chat.model_validate(chat, from_attributes=True)

    @session_factory
    def update_last_message(self, chat_id: int, message_id: int, *, session: Session):
        query = (
            pg_insert(self.ass_model)
            .values({'chat_id': chat_id, 'message_id': message_id})
            .on_conflict_do_update(
                index_elements=[self.ass_model.c.chat_id],
                set_={'message_id': message_id},
            )
            .returning(self.ass_model)
        )
        session.execute(query)
        session.commit()

    @session_factory
    def find_all(self, user_id: int | None = None, type: ChatType | None = None, *, session: Session) -> list[Chat]:
        AliasedLastMessage = aliased(self.messages_model)
        conds = (
            cond_seq()
            .and_(self.model.type == type)
            .and_(self.participant_model.user_id == user_id)
        )

        query = (
            select(self.model)
            .join(self.participant_model)
            .where(conds.clause)
            .options(
                joinedload(self.model.participants),
                joinedload(self.model.last_message),
            )
            .outerjoin(self.ass_model, self.ass_model.c.chat_id == self.model.id)
            .outerjoin(AliasedLastMessage, self.ass_model.c.message_id == AliasedLastMessage.id)
            .order_by(
                desc(AliasedLastMessage.created_at_timestamp),
            )
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
