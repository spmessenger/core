from core.misc.utils.hash import hash_password
from core.misc.auth.jwt import JWTTokenManager
from core.entities import ChatType, User, Chat
from core.repos.abc import AbstractUserRepo
from core.settings import settings
from core.services.messenger import MessengerService


class AuthService:
    def __init__(self, user_repo: AbstractUserRepo, messenger_service: MessengerService):
        self.user_repo = user_repo
        self.messenger_service = messenger_service
        self.jwt_token_manager = JWTTokenManager(
            secret_key=settings.SECRET_KEY,
            algorithm='HS256',
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )

    def login(self, username: str, password: str) -> tuple[User, dict]:
        user = self.user_repo.find_one_by_username(username)
        if user is None:
            raise ValueError(f'User {username} not found')
        if user.hashed_password != hash_password(password):
            raise ValueError('Incorrect password')
        auth = self.get_auth(user.id)
        user = self.user_repo.update(User.Update(id=user.id, refresh_tokens=[*user.refresh_tokens, auth['refresh_token']]))
        return user, auth

    def register(self, username: str, pure_password: str) -> tuple[User, Chat, dict]:
        user = self.user_repo.save(User.Creation(
            username=username,
            hashed_password=hash_password(pure_password)
        ))
        private_chat, _ = self.messenger_service.create_private_chat(user.id)
        auth = self.get_auth(user.id)
        user = self.user_repo.update(User.Update(id=user.id, refresh_tokens=[*user.refresh_tokens, auth['refresh_token']]))
        return user, private_chat, auth

    def refresh_token(self, refresh_token: str) -> dict:
        payload = self.jwt_token_manager.verify_token(refresh_token)
        if payload is None:
            raise ValueError('Invalid refresh token')
        user_id = payload['id']
        user = self.user_repo.get_by_id(user_id)
        if refresh_token not in user.refresh_tokens:
            raise ValueError('Refresh token not found')

        auth = self.get_auth(user.id)
        user.refresh_tokens.remove(refresh_token)
        self.user_repo.update(User.Update(id=user.id, refresh_tokens=[*user.refresh_tokens, auth['refresh_token']]))
        return auth

    def get_auth(self, user_id: int) -> dict:
        access_token = self.jwt_token_manager.create_access_token({'id': user_id})
        refresh_token = self.jwt_token_manager.create_refresh_token({'id': user_id})
        access_token_expiration = self.jwt_token_manager.get_payload(access_token)['exp']
        refresh_token_expiration = self.jwt_token_manager.get_payload(refresh_token)['exp']
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'acess_token_expiration': access_token_expiration,
            'refresh_token_expiration': refresh_token_expiration,
        }
