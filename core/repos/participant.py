from abc import ABC, abstractmethod
from core.entities.participant import Participant
from db.models import Participant as ParticipantModel
from .base import InMemoryRepo, DbRepo


class AbstractParticipantRepo(ABC):
    @abstractmethod
    def find_all_by_user_id(self, user_id: int) -> list[Participant]:
        pass

    @abstractmethod
    def save(self, participant: Participant.Creation) -> Participant:
        pass


class DbParticipantRepo(DbRepo, AbstractParticipantRepo):
    model = ParticipantModel
    entity_model = Participant


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
