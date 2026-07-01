from abc import ABC, abstractmethod

from sqlalchemy import delete, select

from core.entities.reply import Reply
from db.models import Reply as ReplyModel
from db.session import Session, session_factory
from .base import DbRepo, InMemoryRepo


class AbstractReplyRepo(ABC):
    @abstractmethod
    def get_one(self, id: int) -> Reply:
        pass

    @abstractmethod
    def find_one(self, id: int) -> Reply | None:
        pass

    @abstractmethod
    def find_by_replying_msg_id(self, replying_msg_id: int) -> Reply | None:
        pass

    @abstractmethod
    def save(self, reply: Reply.Creation) -> Reply:
        pass

    @abstractmethod
    def delete_one(self, id: int) -> Reply:
        pass


class DbReplyRepo(DbRepo, AbstractReplyRepo):
    model = ReplyModel
    entity_model = Reply

    @session_factory
    def get_one(self, id: int, *, session: Session) -> Reply:
        reply = self.find_one(id=id, session=session)
        if reply is None:
            raise ValueError(f'Reply with id={id} not found')
        return reply

    @session_factory
    def find_one(self, id: int, *, session: Session) -> Reply | None:
        query = select(self.model).where(self.model.id == id)
        reply = session.execute(query).scalar_one_or_none()
        if reply is None:
            return None
        return Reply.model_validate(reply, from_attributes=True)

    @session_factory
    def find_by_replying_msg_id(self, replying_msg_id: int, *, session: Session) -> Reply | None:
        query = select(self.model).where(
            self.model.replying_msg_id == replying_msg_id)
        reply = session.execute(query).scalar_one_or_none()
        if reply is None:
            return None
        return Reply.model_validate(reply, from_attributes=True)

    @session_factory
    def save(self, reply: Reply.Creation, *, session: Session) -> Reply:
        return super().save(reply, session=session)

    @session_factory
    def delete_one(self, id: int, *, session: Session) -> Reply:
        query = (
            delete(self.model)
            .where(self.model.id == id)
            .returning(self.model)
        )
        deleted_model = session.execute(query).scalar_one_or_none()
        if deleted_model is None:
            raise ValueError(f'Reply with id={id} not found')
        session.commit()
        return Reply.model_validate(deleted_model, from_attributes=True)


class InMemoryReplyRepo(AbstractReplyRepo, InMemoryRepo[Reply]):
    def get_one(self, id: int) -> Reply:
        reply = self.find_one(id=id)
        if reply is None:
            raise ValueError(f'Reply with id={id} not found')
        return reply

    def find_one(self, id: int) -> Reply | None:
        return self._find_by('id', id)

    def find_by_replying_msg_id(self, replying_msg_id: int) -> Reply | None:
        return self._find_by('replying_msg_id', replying_msg_id)

    def save(self, reply: Reply.Creation) -> Reply:
        if self.find_by_replying_msg_id(reply.replying_msg_id) is not None:
            raise ValueError(
                f'Reply for replying_msg_id={reply.replying_msg_id} already exists')
        entity = Reply(
            id=0,
            replying_msg_id=reply.replying_msg_id,
            reply_to_msg_id=reply.reply_to_msg_id,
        )
        return self._save(entity)

    def delete_one(self, id: int) -> Reply:
        for index, reply in enumerate(self._storage):
            if reply.id == id:
                return self._storage.pop(index)
        raise ValueError(f'Reply with id={id} not found')
