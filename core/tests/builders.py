from core.services import AuthService, MessengerService
from core.repos import InMemoryChatRepo, InMemoryParticipantRepo, InMemoryUserRepo, InMemoryMessageRepo


def build_messenger_service() -> MessengerService:
    return MessengerService(InMemoryMessageRepo(), InMemoryUserRepo())


def build_auth_service() -> AuthService:
    return AuthService(InMemoryUserRepo(), build_messenger_service())
