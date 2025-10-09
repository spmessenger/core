import pytest
from core.services import AuthService, MessengerService
from .repos import mem_user_repo, mem_chat_repo, mem_message_repo


@pytest.fixture
def mem_messenger_service(mem_user_repo, mem_message_repo):
    return MessengerService(mem_message_repo, mem_user_repo)


@pytest.fixture
def mem_auth_service(mem_user_repo, mem_messenger_service):
    return AuthService(mem_user_repo, mem_messenger_service)
