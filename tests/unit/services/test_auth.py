import pytest
from core.services.auth import AuthService
from core.entities.chat import ChatType
from core.misc.utils.hash import hash_password
from tests.conftest import auth_service as service


def test_register(service: AuthService):
    registered_user, private_chat, auth = service.register(email='test@example.com', verification_code='0000')

    assert registered_user.username == 'test'
    assert registered_user.email == 'test@example.com'
    assert registered_user.hashed_password == hash_password('0000')
    assert len(registered_user.refresh_tokens) == 1
    assert auth['refresh_token'] in registered_user.refresh_tokens

    assert private_chat.type == ChatType.PRIVATE


def test_double_register(service: AuthService):
    service.register(email='test@example.com', verification_code='0000')
    with pytest.raises(ValueError):
        service.register(email='test@example.com', verification_code='0000')


def test_register_and_login(service: AuthService):
    registered_user, private_chat, auth = service.register(email='test@example.com', verification_code='0000')
    assert len(registered_user.refresh_tokens) == 1

    login_user, login_auth = service.login(email='test@example.com', verification_code='0000')

    assert login_user.id == registered_user.id
    assert len(login_user.refresh_tokens) == 2


def test_refresh_token(service: AuthService):
    user, _, auth = service.register(email='test@example.com', verification_code='0000')

    service.refresh_token(auth['refresh_token'])
    user = service.user_repo.get_by_id(user.id)

    assert len(user.refresh_tokens) == 1


def test_update_profile(service: AuthService):
    user, _, _ = service.register(email='test@example.com', verification_code='0000')

    updated_user = service.update_profile(user.id, 'updated')

    assert updated_user.username == 'updated'


def test_update_profile_rejects_blank_username(service: AuthService):
    user, _, _ = service.register(email='test@example.com', verification_code='0000')

    with pytest.raises(ValueError, match='Username cannot be empty'):
        service.update_profile(user.id, '   ')
