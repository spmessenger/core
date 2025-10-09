import pytest
from core.repos.user import InMemoryUserRepo, DbUserRepo, User


def test_save_in_db():
    repo = DbUserRepo()
    user = repo.save(User.Creation(username='test', hashed_password='test'))

    assert user.username == 'test'
    assert user.hashed_password == 'test'


def test_update_in_db():
    repo = DbUserRepo()
    user = repo.save(User.Creation(username='test', hashed_password='test'))
    upd_user = repo.update(User.Update(id=user.id, username='test2', refresh_tokens=['test']))

    assert upd_user.username == 'test2'
    assert upd_user.refresh_tokens == ['test']
    assert upd_user.id == user.id


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
