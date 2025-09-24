from abc import ABC, abstractmethod
from core.entities.participant import Participant
from .base import InMemoryRepo


class AbstractParticipantRepo(ABC):
    @abstractmethod
    def save(self, participant: Participant.Creation) -> Participant:
        pass


class InMemoryParticipantRepo(AbstractParticipantRepo, InMemoryRepo[Participant]):
    def save(self, participant: Participant.Creation) -> Participant:
        entity = Participant(
            id=0,
            chat_id=participant.chat_id,
            user_id=participant.user_id,
        )
        return self._save(entity)