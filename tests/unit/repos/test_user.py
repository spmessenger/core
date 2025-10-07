import pytest
from core.repos.user import InMemoryUserRepo, User


def test_save_in_memory():
    repo = InMemoryUserRepo()
    user = repo.save(User.Creation(username='test', hashed_password='test'))
    assert user.username == 'test'
    assert user.hashed_password == 'test'


def test_get_in_memory():
    repo = InMemoryUserRepo()
    user = repo.save(User.Creation(username='test', hashed_password='test'))
    got_user = repo.get_by_id(user.id)

    assert got_user.id == user.id


def test_get_in_memory_not_found():
    repo = InMemoryUserRepo()
    with pytest.raises(ValueError):
        repo.get_by_id(1)
