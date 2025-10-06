import pytest
from core.tests.utils import clear_in_memory_repos


@pytest.fixture(scope="function", autouse=True)
def clear_in_memory_repos_fixture():
    yield
    clear_in_memory_repos()
