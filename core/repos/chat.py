from abc import ABC, abstractmethod
from datetime import UTC, datetime
from sqlalchemy import Integer, and_, asc, case, delete, desc, func, insert, select, update
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
    def update_last_message(self, chat_id: int, message_id: int | None):
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
    PRIVATE_CHAT_TITLE = '\u0418\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0435'

    @staticmethod
    def _map_chat_model(
        chat_model: ChatModel,
        unread_count: int = 0,
        pin_position: int = 0,
        current_user_id: int | None = None,
    ) -> Chat:
        last_message = getattr(chat_model, 'last_message', None)
        last_message_at: str | None = None
        last_message_text: str | None = None

        if last_message is not None:
            last_message_text = last_message.content
            if last_message.created_at_timestamp is not None:
                last_message_at = datetime.fromtimestamp(
                    float(last_message.created_at_timestamp),
                    tz=UTC,
                ).isoformat()

        title = chat_model.title
        avatar_url = chat_model.avatar_url
        if chat_model.type == ChatType.PRIVATE:
            title = DbChatRepo.PRIVATE_CHAT_TITLE
        elif chat_model.type == ChatType.DIALOG and current_user_id is not None:
            for participant in getattr(chat_model, 'participants', []):
                if participant.user_id == current_user_id:
                    continue
                participant_user = getattr(participant, 'user', None)
                participant_username = getattr(participant_user, 'username', None)
                if participant_username:
                    title = participant_username
                participant_avatar_url = getattr(participant_user, 'avatar_url', None)
                if participant_avatar_url:
                    avatar_url = participant_avatar_url
                if participant_username or participant_avatar_url:
                    break

        return Chat(
            id=chat_model.id,
            type=chat_model.type,
            title=title,
            avatar_url=avatar_url,
            last_message=last_message_text,
            last_message_at=last_message_at,
            unread_messages_count=unread_count,
            pin_position=pin_position,
        )

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
        return self._map_chat_model(chat)

    @session_factory
    def get_by_id(self, chat_id: int, *, session: Session) -> Chat:
        query = (
            select(self.model)
            .where(self.model.id == chat_id)
        )
        chat = session.execute(query).scalar_one_or_none()
        if chat is None:
            raise ValueError(f'Chat with id {chat_id} not found')
        return self._map_chat_model(chat)

    @session_factory
    def update_last_message(self, chat_id: int, message_id: int | None, *, session: Session):
        if message_id is None:
            session.execute(
                delete(self.ass_model).where(self.ass_model.c.chat_id == chat_id)
            )
            session.commit()
            return

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
        return self._map_chat_model(chat)

    @session_factory
    def find_all(self, user_id: int | None = None, type: ChatType | None = None, *, session: Session) -> list[Chat]:
        AliasedChatParticipants = aliased(self.participant_model)
        AliasedLastMessage = aliased(self.messages_model)
        ContextParticipant = aliased(self.participant_model)
        AliasedUser = aliased(self.user_model)

        conds = (
            cond_seq()
            .and_(self.model.type == type)
            .and_(self.participant_model.user_id == user_id)
        )
        unread_messages_count = func.cast(0, Integer)

        if user_id is not None:
            conds.and_(ContextParticipant.chat_visible == True)
            unread_messages_count = func.coalesce(ContextParticipant.unread_messages_count, 0)

        models = (
            self.model,
            ContextParticipant,
            unread_messages_count.label('unread_messages_count'),
        ) if user_id is not None else (self.model,)
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
            is_private_first = case(
                (self.model.type == ChatType.PRIVATE, 0),
                else_=1,
            )
            pinned_group_first = case(
                (ContextParticipant.pin_position > 0, 0),
                else_=1,
            )
            pinned_order_value = case(
                (ContextParticipant.pin_position > 0, ContextParticipant.pin_position),
                else_=None,
            )
            query = (
                query
                .join(
                    ContextParticipant,
                    and_(
                        ContextParticipant.chat_id == self.model.id,
                        ContextParticipant.user_id == user_id
                    )
                )
                .order_by(None)
                .order_by(
                    asc(is_private_first),
                    asc(pinned_group_first),
                    desc(pinned_order_value),
                    desc(AliasedLastMessage.created_at_timestamp),
                    )
            )
        if user_id is None:
            chats = session.execute(query).unique().scalars().all()
            return [self._map_chat_model(chat) for chat in chats]

        rows = session.execute(query).unique().all()
        return [
            self._map_chat_model(
                chat_model,
                int(unread_count or 0),
                int(context_participant.pin_position or 0),
                current_user_id=user_id,
            )
            for chat_model, context_participant, unread_count in rows
        ]

    @session_factory
    def find_all_by_user_id(self, user_id: int, *, session: Session) -> list[Chat]:
        query = (
            select(self.model)
            .join(self.participant_model)
            .where(self.participant_model.user_id == user_id)
            .options(joinedload(self.model.participants))
        )
        chats = session.execute(query).unique().scalars().all()
        return [self._map_chat_model(chat) for chat in chats]


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

    def get_by_id(self, chat_id: int) -> Chat:
        for chat in self._storage:
            if chat.id == chat_id:
                return chat
        raise ValueError(f'Chat with id {chat_id} not found')

    def find_dialog(self, user_id: int, participant_id: int) -> Chat | None:
        chats = self.find_all_by_user_id(user_id)
        participant_chat_ids = {chat.id for chat in self.find_all_by_user_id(participant_id)}
        for chat in chats:
            if chat.id in participant_chat_ids and chat.type == ChatType.DIALOG:
                return chat
        return None

    def find_private_chat(self, user_id: int) -> Chat | None:
        for chat in self.find_all_by_user_id(user_id):
            if chat.type == ChatType.PRIVATE:
                return chat
        return None

    def find_all(self, user_id: int | None = None, type: ChatType | None = None) -> list[Chat]:
        chats = self._storage if user_id is None else self.find_all_by_user_id(user_id)
        if type is not None:
            chats = [chat for chat in chats if chat.type == type]
        return list(chats)

    def update_last_message(self, chat_id: int, message_id: int | None):
        _ = chat_id, message_id
