import pytest
from core.services.messenger import MessengerService


def test_messenger_service():
    message_repo = MessengerService()
    