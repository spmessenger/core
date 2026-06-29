from core.eventbus.event import EventType
from core.eventbus.channels import Channels
from core.eventbus.listener import RedisEventListener
import pytest

from core.entities.chat import ChatType
from core.services import MessengerService
from core.misc.utils.general import id_by_pair
from tests.conftest import messenger_service as messenger


def test_create_private_chat(messenger: MessengerService):
    chat, participant = messenger.create_private_chat(1)

    assert chat.type == ChatType.PRIVATE
    assert participant.chat_id == chat.id
    assert participant.user_id == 1


def test_find_dialog(messenger: MessengerService):
    user_id = 1
    user_id2 = 2
    user_id3 = 3

    chat, *_ = messenger.create_dialog(user_id, user_id2)
    chat1, *_ = messenger.create_dialog(user_id, user_id3)

    dialog = messenger.chat_repo.find_dialog(
        user_id=user_id, participant_id=user_id2)
    dialog1 = messenger.chat_repo.find_dialog(
        user_id=user_id, participant_id=user_id3)

    assert dialog.id == chat.id
    assert dialog1.id == chat1.id

    dialog = messenger.chat_repo.find_dialog(
        user_id=user_id2, participant_id=user_id)
    dialog1 = messenger.chat_repo.find_dialog(
        user_id=user_id3, participant_id=user_id)

    assert dialog.id == chat.id
    assert dialog1.id == chat1.id


def test_create_dialog_001(messenger: MessengerService):
    user_id = 1
    user_id2 = 2
    messenger.create_dialog(user_id, user_id2)

    chats = messenger.chat_repo.find_all(user_id=user_id)

    assert len(chats) == 1
    assert chats[0].type == ChatType.DIALOG

    chats = messenger.chat_repo.find_all(user_id=user_id2)
    assert len(chats) == 0


def test_create_dialog_002(messenger: MessengerService):
    user_id = 1
    user_id2 = 2
    messenger.create_dialog(user_id, user_id2)
    messenger.create_dialog(user_id2, user_id)

    chats = messenger.chat_repo.find_all(user_id=user_id)

    assert len(chats) == 1
    assert chats[0].type == ChatType.DIALOG

    chats = messenger.chat_repo.find_all(user_id=user_id2)
    assert len(chats) == 1

    chats = messenger.chat_repo.find_all()
    assert len(chats) == 1


def test_send_message_to_dialog(messenger: MessengerService):
    user_id = 1
    user_id2 = 2
    chat, _ = messenger.create_dialog(user_id, user_id2)

    chats = messenger.chat_repo.find_all(user_id=user_id2)
    assert len(chats) == 0
    messenger.send_message(chat.id, user_id, 'test')

    chats = messenger.chat_repo.find_all(user_id=user_id2)
    assert len(chats) == 1


def test_send_message(messenger: MessengerService):
    user_id = 1
    chat, participant = messenger.create_private_chat(user_id)

    message = messenger.send_message(chat.id, user_id, 'test')

    assert message.chat_id == chat.id
    assert message.participant_id == participant.id
    assert message.content == 'test'


def test_unread_counter_increments_and_resets_on_connect(messenger: MessengerService):
    user_id = 1
    user_id2 = 2
    chat, _ = messenger.create_dialog(user_id, user_id2)

    messenger.send_message(chat.id, user_id, 'test')
    chats = messenger.chat_repo.find_all(user_id=user_id2)
    assert chats[0].unread_messages_count == 1

    participant, _ = messenger.get_chat_messages(
        chat_id=chat.id, user_id=user_id2)
    assert participant.unread_messages_count == 0

    chats = messenger.chat_repo.find_all(user_id=user_id2)
    assert chats[0].unread_messages_count == 0


def test_unread_counter_does_not_increment_for_connected_users(messenger: MessengerService):
    user_id = 1
    user_id2 = 2
    chat, _ = messenger.create_dialog(user_id, user_id2)

    messenger.send_message(chat.id, user_id, 'test',
                           connected_user_ids={user_id2})

    chats = messenger.chat_repo.find_all(user_id=user_id2)
    assert chats[0].unread_messages_count == 0


def test_pin_unpin_chat(messenger_service: MessengerService):
    user_id = 1
    participant_id = 2

    messenger_service.create_group_chat(
        user_id, title='test', participants=[participant_id])
    messenger_service.create_group_chat(
        user_id, title='test1', participants=[participant_id])

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

    messenger_service.create_group_chat(
        user_id, title='test', participants=[participant_id])
    messenger_service.create_group_chat(
        user_id, title='test1', participants=[participant_id])

    chats = messenger_service.chat_repo.find_all(user_id=user_id)

    assert chats[0].title == 'test'
    assert chats[1].title == 'test1'


@pytest.mark.parametrize(
    ('content', 'expected_video_id'),
    [
        ('https://youtu.be/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
        ('https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
        ('https://www.youtube.com/shorts/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
        ('https://www.youtube.com/embed/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
    ],
)
def test_send_message_enriches_youtube_metadata(
    messenger: MessengerService,
    content: str,
    expected_video_id: str,
):
    user_id = 1
    chat, _ = messenger.create_private_chat(user_id)

    message = messenger.send_message(chat.id, user_id, content)

    assert message.metadata_[
        'youtube']['youtube_video_id'] == expected_video_id


async def test_send_msg(messenger: MessengerService):
    user_id = 1
    chat, _ = messenger.create_private_chat(user_id)
    listener = RedisEventListener(Channels.CHAT, chat_id=chat.id)
    try:
        await listener.listen()
        msg = messenger.send_msg(chat.id, user_id, 'content')
        assert msg.content == 'content'
        event_message = await listener.wait_for_event()
        assert event_message['type'] == 'message.created'
        assert event_message['data']['chat_id'] == chat.id
        assert event_message['data']['message']['id'] == msg.id
        _, messages = messenger.get_chat_messages(chat.id, user_id)
        assert len(messages) == 1
        assert messages[0].content == 'content'
    finally:
        await listener.close()


async def test_unread_msg_count_increased_001(messenger: MessengerService):
    user_id = 1
    chat, _ = messenger.create_private_chat(user_id)
    listener_user = RedisEventListener(Channels.USER, user_id=user_id)
    try:
        await listener_user.listen()
        messenger.send_msg(chat.id, user_id, 'content')
        event = await listener_user.wait_for_event()
        assert event['type'] == EventType.CHAT_UPDATE.value
        assert event['data']['unread_messages_count'] == 1
    finally:
        await listener_user.close()


async def test_unread_msg_count_increased_002(messenger: MessengerService):
    user_id = 1
    chat, participant = messenger.create_private_chat(user_id)
    messenger.activity_service.mark_participant_active(chat.id, participant.id)
    listener_user = RedisEventListener(Channels.USER, user_id=user_id)
    try:
        await listener_user.listen()
        messenger.send_msg(chat.id, user_id, 'content')
        event = await listener_user.wait_for_event()
        assert event['type'] == EventType.CHAT_UPDATE.value
        assert event['data']['unread_messages_count'] == 0
    finally:
        await listener_user.close()
