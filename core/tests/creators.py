from core.entities import User
from core.repos.user import DbUserRepo


def create_user(username, password):
    repo = DbUserRepo()
    return repo.save(User.Creation(username=username, hashed_password=password))
