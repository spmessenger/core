from core.entities import Chat, ChatType, Participant
from core.repos.abc import AbstractChatRepo, AbstractUserRepo, AbstractMessageRepo


class MessengerService:
    def __init__(self, chat_repo: AbstractChatRepo, message_repo: AbstractMessageRepo, user_repo: AbstractUserRepo):
        self.chat_repo = chat_repo
        self.message_repo = message_repo
        self.user_repo = user_repo

    def create_private_chat(self, user_id: int) -> tuple[Chat, Participant]:
        chat = self.chat_repo.find_one(user_id=user_id, type=ChatType.PRIVATE)
        if chat is not None:
            raise ValueError('Private chat already exists')
        return

    def send_message(self, chat_id: int, sender_id: int):
        pass
