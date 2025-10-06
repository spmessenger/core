import pytest
from pydantic import Field
from core.entities.base import Base
from core.repos.base import InMemoryRepo
from core.repos.user import InMemoryUserRepo, User


class ATestBase(Base):
    id: int
    name: str = Field(json_schema_extra=dict(unique=True))


def test_base_repo_check():
    repo = InMemoryRepo[ATestBase]()
    entity = ATestBase(id=1, name="test")
    repo._save(entity)
    with pytest.raises(ValueError, match="Field name is not unique"):
        repo._save(entity)


def test_user_repo():
    repo = InMemoryUserRepo()
    creation = User.Creation(username="test", hashed_password="test")
    repo.save(creation)
    with pytest.raises(ValueError, match="Field username is not unique"):
        repo.save(creation)
