from abc import ABC, abstractmethod
from sqlalchemy import and_, delete, func, insert, select
from sqlalchemy.orm import selectinload
from db.models import (
    ChatGroup as ChatGroupModel,
    Chat as ChatModel,
    Participant as ParticipantModel,
    chat_group_chat_association_table,
)
from db.session import session_factory, Session

from core.entities.chat_group import ChatGroup
from .base import DbRepo, InMemoryRepo


class AbstractChatGroupRepo(ABC):
    @abstractmethod
    def find_all(self, user_id: int) -> list[ChatGroup]:
        pass

    @abstractmethod
    def replace_all(self, user_id: int, groups: list[ChatGroup.Creation]) -> list[ChatGroup]:
        pass


class DbChatGroupRepo(DbRepo, AbstractChatGroupRepo):
    model = ChatGroupModel
    chat_model = ChatModel
    participant_model = ParticipantModel
    ass_model = chat_group_chat_association_table
    entity_model = ChatGroup

    @staticmethod
    def _map_group_model(group_model: ChatGroupModel, unread_messages_count: int = 0) -> ChatGroup:
        return ChatGroup(
            id=group_model.id,
            title=group_model.title,
            user_id=group_model.user_id,
            chat_ids=[chat.id for chat in group_model.chats],
            unread_messages_count=unread_messages_count,
        )

    def _save(self, obj: ChatGroup, session: Session) -> ChatGroupModel:
        db_model = super()._save(obj, session)
        session.flush()
        for chat_id in obj.chat_ids:
            session.execute(
                insert(self.ass_model).values(
                    group_id=db_model.id, chat_id=chat_id)
            )
        return db_model

    def _get_model_dump(self, obj: ChatGroup) -> dict:
        return obj.model_dump(exclude={'id', 'chat_ids'})

    @session_factory
    def find_all(self, user_id: int, *, session: Session) -> list[ChatGroup]:
        total_unread_messages_count = (
            select(func.coalesce(func.sum(self.participant_model.unread_messages_count), 0).label(
                'total_unread_messages_count'))
            .select_from(self.participant_model)
            .where(self.participant_model.user_id == user_id)
        )
        total_unread = session.execute(total_unread_messages_count).scalar_one()
        total_chat_ids_list = list(session.execute(
            select(self.participant_model.chat_id).where(
                self.participant_model.user_id == user_id)
        ).scalars().all())
        sys_group = ChatGroup(
            id=0,
            title='System',
            user_id=user_id,
            chat_ids=total_chat_ids_list,
            unread_messages_count=total_unread,
            type=ChatGroup.Type.SYSTEM,
        )
        unread_messages_count = (
            select(
                func.coalesce(
                    func.sum(self.participant_model.unread_messages_count),
                    0,
                )
            )
            .select_from(self.ass_model)
            .outerjoin(
                self.participant_model,
                and_(
                    self.participant_model.chat_id == self.ass_model.c.chat_id,
                    self.participant_model.user_id == user_id,
                ),
            )
            .where(self.ass_model.c.group_id == self.model.id)
            .scalar_subquery()
        )
        query = (
            select(self.model, unread_messages_count.label(
                'unread_messages_count'))
            .where(self.model.user_id == user_id)
            .options(selectinload(self.model.chats))
            .order_by(self.model.id.asc())
        )
        rows = session.execute(query).unique().all()
        groups = [self._map_group_model(group, int(
            unread_count or 0)) for group, unread_count in rows]
        return [sys_group, *groups]

    @session_factory
    def replace_all(self, user_id: int, groups: list[ChatGroup.Creation], *, session: Session) -> list[ChatGroup]:
        group_ids_query = select(self.model.id).where(
            self.model.user_id == user_id)
        existing_group_ids = list(session.execute(
            group_ids_query).scalars().all())

        if existing_group_ids:
            session.execute(
                delete(self.ass_model).where(
                    self.ass_model.c.group_id.in_(existing_group_ids))
            )
            session.execute(delete(self.model).where(
                self.model.user_id == user_id))

        created_groups: list[ChatGroupModel] = []
        for group in groups:
            group_model = self.model(user_id=user_id, title=group.title)
            session.add(group_model)
            session.flush()
            created_groups.append(group_model)

            if group.chat_ids:
                session.execute(
                    insert(self.ass_model),
                    [{"group_id": group_model.id, "chat_id": chat_id}
                        for chat_id in group.chat_ids],
                )

        session.commit()
        return self.find_all(user_id=user_id, session=session)


class InMemoryChatGroupRepo(AbstractChatGroupRepo, InMemoryRepo[ChatGroup]):
    def find_all(self, user_id: int) -> list[ChatGroup]:
        return [group for group in self._storage if group.user_id == user_id]

    def replace_all(self, user_id: int, groups: list[ChatGroup.Creation]) -> list[ChatGroup]:
        self._storage = [
            group for group in self._storage if group.user_id != user_id]

        for group in groups:
            created_group = ChatGroup(
                id=0,
                title=group.title,
                user_id=user_id,
                chat_ids=list(group.chat_ids),
            )
            self._save(created_group)

        return self.find_all(user_id=user_id)
