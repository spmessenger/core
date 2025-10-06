from core.repos.user import InMemoryUserRepo, User


def test_save_in_memory():
    repo = InMemoryUserRepo()
    user = repo.save(User.Creation(username='test', hashed_password='test'))
    assert user.username == 'test'
    assert user.hashed_password == 'test'
