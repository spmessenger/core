from abc import ABC, abstractmethod
from sqlalchemy import and_, asc, desc, insert, select, update
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy.dialects.postgresql import insert as pg_insert
from db.models import Chat as ChatModel, Participant as ParticipantModel, Message as MessageModel, User as UserModel, chat_last_message_association_table
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
    def find_dialog(self, user_id: int, participant_id: int) -> Chat | None:
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
    user_model = UserModel
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
    def find_dialog(self, user_id: int, participant_id: int, *, session: Session) -> Chat | None:
        # Create aliases for the two participants we're looking for
        UserParticipant = aliased(self.participant_model)
        OtherParticipant = aliased(self.participant_model)

        # Find dialogs that have both the current user AND the other participant
        query = (
            select(self.model)
            .join(UserParticipant, UserParticipant.chat_id == self.model.id)
            .join(OtherParticipant, OtherParticipant.chat_id == self.model.id)
            .where(
                self.model.type == ChatType.DIALOG,
                UserParticipant.user_id == user_id,
                OtherParticipant.user_id == participant_id
            )
        )

        chat = session.execute(query).scalar_one_or_none()
        if chat is None:
            return None
        return Chat.model_validate(chat, from_attributes=True)

    @session_factory
    def find_all(self, user_id: int | None = None, type: ChatType | None = None, with_user: bool = False, *, session: Session) -> list[Chat]:
        # if user_id is None and with_user is True:
        #     raise ValueError('You cannot get chats with user_id=None and with_user=True')

        AliasedChatParticipants = aliased(self.participant_model)
        AliasedLastMessage = aliased(self.messages_model)
        ContextParticipant = aliased(self.participant_model)
        AliasedUser = aliased(self.user_model)

        conds = (
            cond_seq()
            .and_(self.model.type == type)
            .and_(self.participant_model.user_id == user_id)
        )

        if user_id is not None:
            conds.and_(self.participant_model.user_id == user_id).and_(ContextParticipant.chat_visible == True)

        models = (self.model, ContextParticipant) if user_id is not None else (self.model,)
        query = (
            select(*models)
            .join(self.participant_model)
            .where(conds.clause)
            .options(
                joinedload(self.model.last_message),
                joinedload(self.model.participants.of_type(AliasedChatParticipants)).joinedload(
                    AliasedChatParticipants.user.of_type(AliasedUser)),
            )
            .outerjoin(self.ass_model, self.ass_model.c.chat_id == self.model.id)
            .outerjoin(AliasedLastMessage, self.ass_model.c.message_id == AliasedLastMessage.id)
            .order_by(
                desc(AliasedLastMessage.created_at_timestamp),
            )
        )
        if user_id is not None:
            query = (
                query
                .join(
                    ContextParticipant,
                    and_(
                        ContextParticipant.chat_id == self.model.id,
                        ContextParticipant.user_id == user_id
                    )
                )
                .order_by(
                    asc(ContextParticipant.pin_position == 0),
                    asc(ContextParticipant.pin_position),
                )
            )
        chats = session.execute(query).unique().scalars().all()
        # for chat in chats:
        #     if chat.type != ChatType.DIALOG:
        #         continue
        #     chat.title = list(filter(lambda p: p.user_id != user_id, chat.participants)).pop().user.username
        return [Chat.model_validate(chat, from_attributes=True) for chat in chats]

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
            avatar_url=chat.avatar_url,
        )
        return self._save(entity)
