import pytest
from core.repos.user import InMemoryUserRepo
from core.repos.chat import InMemoryChatRepo
from core.repos.participant import InMemoryParticipantRepo
from core.repos.message import InMemoryMessageRepo


@pytest.fixture(scope="function")
def clear_in_memory_repos():
    yield
    InMemoryUserRepo._storage.clear()
    InMemoryChatRepo._storage.clear()
    InMemoryParticipantRepo._storage.clear()
    InMemoryMessageRepo._storage.clear()
