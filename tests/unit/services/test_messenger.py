from core.entities.chat import ChatType
from core.services import MessengerService
from tests.conftest import messenger_service as messenger


def test_create_private_chat(messenger: MessengerService):
    chat, participant = messenger.create_private_chat(1)

    assert chat.type == ChatType.PRIVATE
    assert participant.chat_id == chat.id
    assert participant.user_id == 1


def test_send_message(messenger: MessengerService):
    user_id = 1
    chat, participant = messenger.create_private_chat(user_id)

    message = messenger.send_message(chat.id, user_id, 'test')

    assert message.chat_id == chat.id
    assert message.participant_id == participant.id
    assert message.content == 'test'
