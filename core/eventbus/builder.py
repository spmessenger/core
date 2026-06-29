from core.entities.chat import Chat
from core.entities.message import Message
from core.eventbus.event import EventType


class EventPayloadBuilder:
    @classmethod
    def message_created(cls, chat_id: int, message: Message) -> dict:
        return {
            'type': EventType.MESSAGE_CREATED.value,
            'data': {
                'chat_id': chat_id,
                'message': message.model_dump(mode='json'),
            }
        }

    @classmethod
    def chat_update(cls, update: Chat.EventUpdate) -> dict:
        return {
            'type': EventType.CHAT_UPDATE.value,
            'data': update.model_dump(mode='json', exclude_unset=True),
        }
