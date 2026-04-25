from core.misc.utils.hash import hash_password
from core.misc.auth.jwt import JWTTokenManager
from core.entities import User, Chat
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

    def _normalize_email(self, email: str | None) -> str | None:
        if email is None:
            return None
        normalized = email.strip().lower()
        if not normalized:
            return None
        if '@' not in normalized or normalized.startswith('@') or normalized.endswith('@'):
            raise ValueError('Invalid email')
        return normalized

    def _normalize_username(self, username: str) -> str:
        normalized = username.strip()
        if not normalized:
            raise ValueError('Username cannot be empty')
        return normalized

    def _normalize_password(self, password: str) -> str:
        normalized = password.strip()
        if not normalized:
            raise ValueError('Password cannot be empty')
        return normalized

    def login(self, username: str, password: str) -> tuple[User, dict]:
        normalized_username = self._normalize_username(username)
        normalized_password = self._normalize_password(password)
        user = self.user_repo.find_one_by_username(normalized_username)
        if user is None:
            raise ValueError(f'User with username {normalized_username} not found')
        if user.hashed_password != hash_password(normalized_password):
            raise ValueError('Incorrect password')
        auth = self.get_auth(user.id)
        user = self.user_repo.update(User.Update(id=user.id, refresh_tokens=[*user.refresh_tokens, auth['refresh_token']]))
        return user, auth

    def register(self, username: str, password: str) -> tuple[User, Chat, dict]:
        normalized_username = self._normalize_username(username)
        normalized_password = self._normalize_password(password)
        if self.user_repo.find_one_by_username(normalized_username) is not None:
            raise ValueError(f'User with username {normalized_username} already exists')
        user = self.user_repo.save(User.Creation(
            username=normalized_username,
            email=None,
            hashed_password=hash_password(normalized_password),
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

    def update_profile(
        self,
        user_id: int,
        username: str | None = None,
        email: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        user = self.user_repo.get_by_id(user_id)
        next_username = user.username
        if username is not None:
            normalized_username = username.strip()
            if not normalized_username:
                raise ValueError('Username cannot be empty')
            next_username = normalized_username

        next_email = user.email
        if email is not None:
            normalized_email = self._normalize_email(email)
            next_email = user.email if normalized_email is None else normalized_email

        if user.username == next_username and user.avatar_url == avatar_url and user.email == next_email:
            return user

        return self.user_repo.update(
            User.Update(
                id=user.id,
                username=next_username,
                email=next_email,
                avatar_url=avatar_url,
            )
        )

    def set_subscription_tier(self, user_id: int, tier: str) -> User:
        normalized_tier = tier.strip().lower()
        if normalized_tier not in {'free', 'premium'}:
            raise ValueError('Unsupported subscription tier')
        user = self.user_repo.get_by_id(user_id)
        if user.subscription_tier == normalized_tier:
            return user
        return self.user_repo.update(
            User.Update(
                id=user.id,
                subscription_tier=normalized_tier,
            )
        )

    def set_youtube_assisted_enabled(self, user_id: int, enabled: bool) -> User:
        user = self.user_repo.get_by_id(user_id)
        if user.youtube_assisted_enabled == enabled:
            return user
        return self.user_repo.update(
            User.Update(
                id=user.id,
                youtube_assisted_enabled=enabled,
            )
        )

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
