from core.entities.chat import Chat
from core.entities.message import Message
from core.eventbus.channels import Channels
from core.eventbus.publisher import EventPublisher
from core.eventbus.builder import EventPayloadBuilder


class MessengerNotifier:

    def __init__(self, puslisher: EventPublisher):
        self.puslisher = puslisher

    def notify_new_message(self, chat_id: int, message: Message) -> None:
        self.puslisher.publish(
            Channels.CHAT.build(chat_id=chat_id),
            EventPayloadBuilder.message_created(chat_id, message),
        )

    def notify_chat_update(self, user_id: int, update: Chat.EventUpdate) -> None:
        self.puslisher.publish(
            Channels.USER.build(user_id=user_id),
            EventPayloadBuilder.chat_update(update),
        )
