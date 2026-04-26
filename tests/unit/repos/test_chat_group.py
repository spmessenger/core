from core.repos.chat_group import DbChatGroupRepo
from core.repos.chat import DbChatRepo
from core.repos.participant import DbParticipantRepo
from core.entities.chat_group import ChatGroup
from core.entities.chat import Chat, ChatType
from core.entities.participant import Participant
from core.tests.creators import create_user


def test_get_all():
    user = create_user('test', 'test')
    chat = DbChatRepo().save(Chat.Creation(type=ChatType.PRIVATE, title='test'))
    repo = DbChatGroupRepo()
    group = repo.save(ChatGroup.Creation(
        user_id=user.id, title='test', chat_ids=[chat.id]))
    got_groups = repo.find_all(user_id=user.id)

    assert len(got_groups) == 2
    assert got_groups[1].id == group.id
    assert got_groups[1].title == 'test'
    assert got_groups[1].chat_ids == [chat.id]


def test_get_all_returns_sql_summed_unread_messages_count():
    user = create_user('owner', 'test')
    first_chat = DbChatRepo().save(Chat.Creation(type=ChatType.GROUP, title='first'))
    second_chat = DbChatRepo().save(Chat.Creation(type=ChatType.GROUP, title='second'))

    participant_repo = DbParticipantRepo()
    participant_repo.save(
        Participant.MemberCreation(
            chat_id=first_chat.id,
            user_id=user.id,
            unread_messages_count=2,
        )
    )
    participant_repo.save(
        Participant.MemberCreation(
            chat_id=second_chat.id,
            user_id=user.id,
            unread_messages_count=3,
        )
    )

    repo = DbChatGroupRepo()
    repo.save(
        ChatGroup.Creation(
            user_id=user.id,
            title='unread',
            chat_ids=[first_chat.id, second_chat.id],
        )
    )

    got_groups = repo.find_all(user_id=user.id)

    assert len(got_groups) == 2
    assert got_groups[0].unread_messages_count == 5


def test_get_all_returns_all_groups_for_user():
    user = create_user('owner', 'test')
    first_chat = DbChatRepo().save(Chat.Creation(type=ChatType.GROUP, title='first'))
    second_chat = DbChatRepo().save(Chat.Creation(type=ChatType.GROUP, title='second'))

    repo = DbChatGroupRepo()
    first_group = repo.save(
        ChatGroup.Creation(
            user_id=user.id,
            title='filled',
            chat_ids=[first_chat.id, second_chat.id],
        )
    )
    second_group = repo.save(
        ChatGroup.Creation(
            user_id=user.id,
            title='empty',
            chat_ids=[],
        )
    )

    got_groups = repo.find_all(user_id=user.id)

    assert [group.id for group in got_groups] == [0, first_group.id, second_group.id]
    assert got_groups[1].chat_ids == [first_chat.id, second_chat.id]
    assert got_groups[2].chat_ids == []
