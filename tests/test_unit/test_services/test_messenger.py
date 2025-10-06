from core.services.messenger import MessengerService
from core.repos.message import InMemoryMessageRepo
from core.repos.user import InMemoryUserRepo


def test_messenger_service():
    messenger = MessengerService(InMemoryMessageRepo(), InMemoryUserRepo())
    messenger.send_message(chat_id=1, sender_id=1)
