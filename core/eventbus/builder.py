from core.entities.message import Message
from core.eventbus.event import EventType


class EventPayloadBuilder:
    @classmethod
    def message_created(cls, chat_id: int, message: Message) -> dict:
        return {
            'type': EventType.MESSAGE_CREATED.value,
            'chat_id': chat_id,
            'message': message.model_dump(mode='json'),
        }
