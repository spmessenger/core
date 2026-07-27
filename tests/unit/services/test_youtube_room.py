from core.entities.message import Message
from core.repos.message import InMemoryMessageRepo


def test_assign_youtube_room_preserves_existing_message_metadata():
    repo = InMemoryMessageRepo()
    message = repo._save(
        Message(
            id=0,
            chat_id=1,
            participant_id=1,
            metadata_={
                'youtube': {'youtube_video_id': 'abc123'},
                'custom': {'keep': True},
                'rooms': {'other': 10},
            },
            content='https://youtu.be/abc123',
            created_at_timestamp=1,
        )
    )

    repo.assign_youtube_room(message.id, 20)

    updated_message = repo.get_one(message.id)
    assert updated_message.metadata_ == {
        'youtube': {'youtube_video_id': 'abc123'},
        'custom': {'keep': True},
        'rooms': {
            'other': 10,
            'youtube': 20,
        },
    }
