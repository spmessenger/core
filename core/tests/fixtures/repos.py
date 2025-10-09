import pytest
from core.repos import InMemoryChatRepo, InMemoryParticipantRepo, InMemoryUserRepo, InMemoryMessageRepo


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
