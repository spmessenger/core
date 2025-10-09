from core.services import MessengerService
from tests.conftest import mem_messenger_service as messenger


def test_messenger_service(messenger: MessengerService):
    messenger.create_private_chat(1)
