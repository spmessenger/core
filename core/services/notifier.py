from core.entities.message import Message
from core.eventbus.channels import Channels
from core.eventbus.engine import EventPublisher
from core.eventbus.builder import EventPayloadBuilder


class MessengerNotifier:

    def __init__(self, puslisher: EventPublisher):
        self.puslisher = puslisher

    def notify_new_message(self, chat_id: int, message: Message) -> None:
        self.puslisher.publish(
            Channels.CHAT.build(chat_id=chat_id),
            EventPayloadBuilder.message_created(chat_id, message),
        )
