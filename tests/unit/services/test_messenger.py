from core.entities.chat import ChatType
from core.services import MessengerService
from tests.conftest import messenger_service as messenger


def test_create_private_chat(messenger: MessengerService):
    chat, participant = messenger.create_private_chat(1)

    assert chat.type == ChatType.PRIVATE
    assert participant.chat_id == chat.id
    assert participant.user_id == 1


def test_create_dialog(messenger: MessengerService):
    user_id = 1
    user_id2 = 2
    messenger.create_dialog(user_id, user_id2)

    chats = messenger.chat_repo.find_all(user_id=user_id)

    assert len(chats) == 1
    assert chats[0].type == ChatType.DIALOG

    chats = messenger.chat_repo.find_all(user_id=user_id2)
    assert len(chats) == 0


def test_send_message(messenger: MessengerService):
    user_id = 1
    chat, participant = messenger.create_private_chat(user_id)

    message = messenger.send_message(chat.id, user_id, 'test')

    assert message.chat_id == chat.id
    assert message.participant_id == participant.id
    assert message.content == 'test'


def test_pin_unpin_chat(messenger_service: MessengerService):
    user_id = 1
    participant_id = 2

    messenger_service.create_group_chat(user_id, title='test', participants=[participant_id])
    messenger_service.create_group_chat(user_id, title='test1', participants=[participant_id])

    chats = messenger_service.chat_repo.find_all(user_id=user_id)

    assert chats[0].title == 'test'
    assert chats[1].title == 'test1'

    pinned = messenger_service.pin_chat(chats[1].id, user_id)
    assert pinned is True

    chats = messenger_service.chat_repo.find_all(user_id=user_id)
    assert chats[0].title == 'test1'
    assert chats[1].title == 'test'

    unpinned = messenger_service.unpin_chat(chats[0].id, user_id)
    assert unpinned is True

    chats = messenger_service.chat_repo.find_all(user_id=user_id)
    assert chats[0].title == 'test'
    assert chats[1].title == 'test1'


def test_chat_shuffle_001(messenger_service: MessengerService):
    user_id = 1
    participant_id = 2

    messenger_service.create_group_chat(user_id, title='test', participants=[participant_id])
    messenger_service.create_group_chat(user_id, title='test1', participants=[participant_id])

    chats = messenger_service.chat_repo.find_all(user_id=user_id)

    assert chats[0].title == 'test'
    assert chats[1].title == 'test1'

    messenger_service.send_message(chats[1].id, user_id, 'test')

    chats = messenger_service.chat_repo.find_all(user_id=user_id)

    assert chats[0].title == 'test1'
    assert chats[1].title == 'test'

    messenger_service.send_message(chats[1].id, user_id, 'test')

    chats = messenger_service.chat_repo.find_all(user_id=user_id)

    assert chats[0].title == 'test'
    assert chats[1].title == 'test1'
