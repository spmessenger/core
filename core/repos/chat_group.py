from abc import ABC, abstractmethod
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import joinedload
from db.models import ChatGroup as ChatGroupModel, chat_group_chat_association_table
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
    ass_model = chat_group_chat_association_table
    entity_model = ChatGroup

    @staticmethod
    def _map_group_model(group_model: ChatGroupModel) -> ChatGroup:
        return ChatGroup(
            id=group_model.id,
            title=group_model.title,
            user_id=group_model.user_id,
            chat_ids=[chat.id for chat in group_model.chats],
        )

    @session_factory
    def find_all(self, user_id: int, *, session: Session) -> list[ChatGroup]:
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .options(joinedload(self.model.chats))
            .order_by(self.model.id.asc())
        )
        groups = session.execute(query).unique().scalars().all()
        return [self._map_group_model(group) for group in groups]

    @session_factory
    def replace_all(self, user_id: int, groups: list[ChatGroup.Creation], *, session: Session) -> list[ChatGroup]:
        group_ids_query = select(self.model.id).where(self.model.user_id == user_id)
        existing_group_ids = list(session.execute(group_ids_query).scalars().all())

        if existing_group_ids:
            session.execute(
                delete(self.ass_model).where(self.ass_model.c.group_id.in_(existing_group_ids))
            )
            session.execute(delete(self.model).where(self.model.user_id == user_id))

        created_groups: list[ChatGroupModel] = []
        for group in groups:
            group_model = self.model(user_id=user_id, title=group.title)
            session.add(group_model)
            session.flush()
            created_groups.append(group_model)

            if group.chat_ids:
                session.execute(
                    insert(self.ass_model),
                    [{"group_id": group_model.id, "chat_id": chat_id} for chat_id in group.chat_ids],
                )

        session.commit()
        return self.find_all(user_id=user_id, session=session)


class InMemoryChatGroupRepo(AbstractChatGroupRepo, InMemoryRepo[ChatGroup]):
    def find_all(self, user_id: int) -> list[ChatGroup]:
        return [group for group in self._storage if group.user_id == user_id]

    def replace_all(self, user_id: int, groups: list[ChatGroup.Creation]) -> list[ChatGroup]:
        self._storage = [group for group in self._storage if group.user_id != user_id]

        for group in groups:
            created_group = ChatGroup(
                id=0,
                title=group.title,
                user_id=user_id,
                chat_ids=list(group.chat_ids),
            )
            self._save(created_group)

        return self.find_all(user_id=user_id)
