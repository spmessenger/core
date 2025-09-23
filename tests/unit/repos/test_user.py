from core.repos.user import InMemoryUserRepo, User


def test_save_in_memory():
    repo = InMemoryUserRepo()
    user = repo.save(User.Creation(name="John", phone="123456789"))
    assert user.name == "John"
    assert user.phone == "123456789"
