import pytest
from core.tests.utils import clear_in_memory_repos
from core.services import AuthService, MessengerService
from core.repos import InMemoryChatRepo, InMemoryParticipantRepo, InMemoryUserRepo, InMemoryMessageRepo
from db.misc import create_tables, drop_tables


@pytest.fixture(scope='function', autouse=True)
def create_and_drop_tables():
    create_tables()
    yield
    drop_tables()


@pytest.fixture(scope="function", autouse=True)
def clear_in_memory_repos_fixture():
    yield
    clear_in_memory_repos()


@pytest.fixture
def mem_message_repo():
    return InMemoryMessageRepo()


@pytest.fixture
def mem_chat_repo():
    return InMemoryChatRepo()


@pytest.fixture
def mem_participant_repo():
    return InMemoryParticipantRepo()


@pytest.fixture
def mem_user_repo():
    return InMemoryUserRepo()


@pytest.fixture
def mem_messenger_service(mem_chat_repo, mem_user_repo, mem_message_repo):
    return MessengerService(mem_chat_repo, mem_message_repo, mem_user_repo)


@pytest.fixture
def mem_auth_service(mem_user_repo, mem_messenger_service):
    return AuthService(mem_user_repo, mem_messenger_service)
