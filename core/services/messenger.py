from core.repos.message import AbstractMessageRepo

class MessengerService:
    def __init__(self, message_repo: AbstractMessageRepo):
        self.message_repo = message_repo
