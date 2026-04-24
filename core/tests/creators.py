from core.entities import User
from core.repos.user import DbUserRepo


def create_user(username, password, email=None):
    repo = DbUserRepo()
    resolved_email = email or f'{username}@example.com'
    return repo.save(User.Creation(username=username, email=resolved_email, hashed_password=password))
