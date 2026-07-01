from core.entities.chat import Chat
from core.entities.message import Message
from core.entities.participant import Participant
from core.entities.reply import Reply
from core.repos.chat import DbChatRepo
from core.repos.message import DbMessageRepo
from core.repos.participant import DbParticipantRepo
from core.repos.reply import DbReplyRepo, InMemoryReplyRepo
from core.tests.creators import create_user


def test_save_and_find_by_replying_msg_id_in_db():
    user = create_user('reply-owner', 'test')
    chat = DbChatRepo().save(Chat.PrivateChatCreation())
    participant = DbParticipantRepo().save(
        Participant.MemberCreation(chat_id=chat.id, user_id=user.id)
    )
    message_repo = DbMessageRepo()
    original = message_repo.save(
        Message.Creation(
            chat_id=chat.id,
            participant_id=participant.id,
            content='original',
        )
    )
    replying = message_repo.save(
        Message.Creation(
            chat_id=chat.id,
            participant_id=participant.id,
            content='replying',
        )
    )

    repo = DbReplyRepo()
    reply = repo.save(
        Reply.Creation(
            replying_msg_id=replying.id,
            reply_to_msg_id=original.id,
        )
    )

    got_reply = repo.find_by_replying_msg_id(replying.id)

    assert got_reply == reply


def test_save_and_find_by_replying_msg_id_in_memory():
    repo = InMemoryReplyRepo()
    reply = repo.save(
        Reply.Creation(
            replying_msg_id=1,
            reply_to_msg_id=2,
        )
    )

    got_reply = repo.find_by_replying_msg_id(1)

    assert got_reply == reply
