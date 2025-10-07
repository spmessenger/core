from core.misc.utils.hash import hash_password
from core.misc.auth.jwt import JWTTokenManager
from core.repos.user import AbstractUserRepo, User
from core.repos.chat import AbstractChatRepo, Chat
from core.repos.participant import AbstractParticipantRepo
from core.entities.chat import ChatType
from core.settings import settings


class AuthService:
    def __init__(self, user_repo: AbstractUserRepo, chat_repo: AbstractChatRepo, participant_repo: AbstractParticipantRepo):
        self.chat_repo = chat_repo
        self.user_repo = user_repo
        self.participant_repo = participant_repo
        self.jwt_token_manager = JWTTokenManager(
            secret_key=settings.SECRET_KEY,
            algorithm='HS256',
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )

    def login(self, username: str, password: str) -> tuple[User, dict]:
        user = self.user_repo.find_by_username(username)
        if user is None:
            raise ValueError(f'User {username} not found')
        if user.hashed_password != hash_password(password):
            raise ValueError('Incorrect password')
        auth = self.get_auth(user.id)
        self.user_repo.update(User.Update(id=user.id, refresh_tokens=[*user.refresh_tokens, auth['refresh_token']]))
        return user, auth

    def register(self, username: str, pure_password: str) -> tuple[User, Chat, dict]:
        user = self.user_repo.save(User.Creation(
            username=username,
            hashed_password=hash_password(pure_password)
        ))
        private_chat = self.chat_repo.save(
            Chat.Creation(type=ChatType.PRIVATE))
        auth = self.get_auth(user.id)
        self.user_repo.update(User.Update(id=user.id, refresh_tokens=[*user.refresh_tokens, auth['refresh_token']]))
        return user, private_chat, auth

    def refresh_token(self, refresh_token: str) -> dict:
        payload = self.jwt_token_manager.verify_token(refresh_token)
        if payload is None:
            raise ValueError('Invalid refresh token')
        user_id = payload['id']
        user = self.user_repo.find_by_id(user_id)
        if user is None:
            raise ValueError('User not found')

        auth = self.get_auth(user.id)
        user.refresh_tokens.remove(refresh_token)
        self.user_repo.update(User.Update(id=user.id, refresh_tokens=[*user.refresh_tokens, auth['refresh_token']]))
        return auth

    def get_auth(self, user_id: int) -> dict:
        return {
            'access_token': self.jwt_token_manager.create_access_token({'id': user_id}),
            'refresh_token': self.jwt_token_manager.create_refresh_token({'id': user_id})
        }
