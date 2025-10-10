from core.repos.chat import DbChatRepo, Chat, ChatType


def test_save():
    repo = DbChatRepo()
    chat = repo.save(Chat.Creation(type=ChatType.PRIVATE, title='test'))

    assert chat.type == ChatType.PRIVATE
    assert chat.title == 'test'


def test_get_by_id():
    repo = DbChatRepo()
    chat = repo.save(Chat.Creation(type=ChatType.PRIVATE, title='test'))
    got_chat = repo.get_by_id(chat.id)

    assert got_chat.id == chat.id
    assert got_chat.type == ChatType.PRIVATE
    assert got_chat.title == 'test'
