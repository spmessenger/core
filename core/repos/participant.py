from abc import ABC, abstractmethod
from sqlalchemy import func, select, update

from core.entities.participant import Participant
from db.models import Participant as ParticipantModel
from db.session import session_factory, Session
from db.misc.cond import cond_seq
from .base import InMemoryRepo, DbRepo


class AbstractParticipantRepo(ABC):
    @abstractmethod
    def get_one(self, id: int | None = None, chat_id: int | None = None, user_id: int | None = None) -> Participant:
        pass

    @abstractmethod
    def find_one(self, id: int | None = None, chat_id: int | None = None, user_id: int | None = None) -> Participant | None:
        pass

    @abstractmethod
    def find_all(self, user_id: int | None = None, chat_id: int | None = None) -> list[Participant]:
        pass

    @abstractmethod
    def get_max_pin_position(self, user_id: int) -> int:
        pass

    @abstractmethod
    def update(self, participant: Participant.Update) -> Participant:
        pass

    @abstractmethod
    def update_chat_visible_to_all(self, chat_id: int, visible: bool) -> list[Participant]:
        pass

    @abstractmethod
    def save(self, participant: Participant.Creation) -> Participant:
        pass


class DbParticipantRepo(DbRepo, AbstractParticipantRepo):
    model = ParticipantModel
    entity_model = Participant

    @session_factory
    def get_max_pin_position(self, user_id: int, *, session: Session) -> int:
        query = (
            select(func.max(self.model.pin_position))
            .where(self.model.user_id == user_id)
        )
        return (session.execute(query)).scalar_one() or 0

    @session_factory
    def get_one(self, id: int | None = None, chat_id: int | None = None, user_id: int | None = None, *, session: Session) -> Participant:
        conds = (
            cond_seq()
            .and_(self.model.id == id)
            .and_(self.model.chat_id == chat_id)
            .and_(self.model.user_id == user_id)
        )
        query = (
            select(self.model)
            .where(*conds.and_clauses)
        )
        participant = session.execute(query).scalar_one_or_none()
        if participant is None:
            raise ValueError(f'Participant with id {id} not found')
        return Participant.model_validate(participant, from_attributes=True)

    @session_factory
    def find_one(self, id: int | None = None, chat_id: int | None = None, user_id: int | None = None, *, session: Session) -> Participant | None:
        conds = (
            cond_seq()
            .and_(self.model.id == id)
            .and_(self.model.chat_id == chat_id)
            .and_(self.model.user_id == user_id)
        )
        query = (
            select(self.model)
            .where(*conds.and_clauses)
        )
        participant = session.execute(query).scalar_one_or_none()
        if participant is None:
            return None
        return Participant.model_validate(participant, from_attributes=True)

    @session_factory
    def find_all(self, user_id: int | None = None, chat_id: int | None = None, *, session: Session) -> list[Participant]:
        conds = (
            cond_seq()
            .and_(self.model.user_id == user_id)
            .and_(self.model.chat_id == chat_id)
        )
        query = (
            select(self.model)
            .where(*conds.clauses)
        )
        participants = session.execute(query).unique().scalars().all()
        return [Participant.model_validate(participant, from_attributes=True) for participant in participants]

    @session_factory
    def update(self, participant: Participant.Update, *, session: Session) -> Participant:
        return super().update(participant, session=session)

    @session_factory
    def update_chat_visible_to_all(self, chat_id: int, visible: bool, *, session: Session) -> list[Participant]:
        query = (
            update(self.model)
            .values(chat_visible=visible)
            .where(self.model.chat_id == chat_id)
            .returning(self.model)
        )
        result = session.execute(query).scalars()
        paritcipants = [Participant.model_validate(participant, from_attributes=True) for participant in result]
        session.commit()
        return paritcipants

    @session_factory
    def save(self, participant: Participant.Creation, *, session: Session) -> Participant:
        return super().save(participant, session=session)


class InMemoryParticipantRepo(AbstractParticipantRepo, InMemoryRepo[Participant]):
    def find_all_by_user_id(self, user_id: int) -> list[Participant]:
        return [ent for ent in self._storage if ent.user_id == user_id]

    def save(self, participant: Participant.Creation) -> Participant:
        entity = Participant(
            id=0,
            chat_id=participant.chat_id,
            user_id=participant.user_id,
        )
        return self._save(entity)
