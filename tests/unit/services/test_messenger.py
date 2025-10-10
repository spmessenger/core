from core.entities.chat import ChatType
from core.services import MessengerService
from tests.conftest import messenger_service as messenger


def test_messenger_service(messenger: MessengerService):
    chat, participant = messenger.create_private_chat(1)

    assert chat.type == ChatType.PRIVATE
    assert participant.chat_id == chat.id
    assert participant.user_id == 1
