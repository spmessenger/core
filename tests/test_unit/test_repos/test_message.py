from core.repos.message import InMemoryMessageRepo, Message


def test_save_in_memory():
    repo = InMemoryMessageRepo()
    message = repo.save(Message.Creation(
        chat_id=1, participant_id=1, content="Hello"))
    assert message.chat_id == 1
    assert message.participant_id == 1
    assert message.content == "Hello"
