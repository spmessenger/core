from core.services.auth import RegistrationService
from core.repos.user import InMemoryUserRepo
from core.repos.chat import InMemoryChatRepo
from core.repos.participant import InMemoryParticipantRepo
from core.entities.chat import ChatType
from core.misc.utils.hash import hash_password

def test_register():
    service = RegistrationService(InMemoryUserRepo(), InMemoryChatRepo(), InMemoryParticipantRepo())
    registered_user, private_chat = service.register(username='test', pure_password='test')

    assert registered_user.username == 'test'
    assert registered_user.hashed_password == hash_password('test')

    assert private_chat.type == ChatType.PRIVATE