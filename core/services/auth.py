from core.misc.utils.hash import hash_password
from core.repos.user import AbstractUserRepo, User
from core.repos.chat import AbstractChatRepo, Chat
from core.repos.participant import AbstractParticipantRepo
from core.entities.chat import ChatType


class AuthService:
    def __init__(self, user_repo: AbstractUserRepo, chat_repo: AbstractChatRepo, participant_repo: AbstractParticipantRepo):
        self.chat_repo = chat_repo
        self.user_repo = user_repo
        self.participant_repo = participant_repo

    def login(self, username: str, password: str) -> User:
        user = self.user_repo.find_by_username(username)
        if user is None:
            raise ValueError(f"User {username} not found")
        if user.hashed_password != hash_password(password):
            raise ValueError("Incorrect password")
        return user

    def register(self, username: str, pure_password: str) -> tuple[User, Chat]:
        user = self.user_repo.save(User.Creation(
            username=username,
            hashed_password=hash_password(pure_password)
        ))
        private_chat = self.chat_repo.save(
            Chat.Creation(type=ChatType.PRIVATE))
        return user, private_chat
