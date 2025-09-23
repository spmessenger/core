from core.entities.user import UserId
from core.repos.message import AbstractMessageRepo
from core.repos.user import AbstractUserRepo


class MessengerService:
    def __init__(self, message_repo: AbstractMessageRepo, user_repo: AbstractUserRepo):
        self.message_repo = message_repo
        self.user_repo = user_repo

    def send_message(self, chat_id: int, sender_id: UserId):
        pass
