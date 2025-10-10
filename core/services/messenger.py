from core.entities import Chat, ChatType, Participant, Message
from core.repos.abc import AbstractChatRepo, AbstractParticipantRepo, AbstractUserRepo, AbstractMessageRepo


class MessengerService:
    def __init__(
        self,
        chat_repo: AbstractChatRepo,
        participant_repo: AbstractParticipantRepo,
        message_repo: AbstractMessageRepo,
        user_repo: AbstractUserRepo
    ):
        self.chat_repo = chat_repo
        self.participant_repo = participant_repo
        self.message_repo = message_repo
        self.user_repo = user_repo

    def create_private_chat(self, user_id: int) -> tuple[Chat, Participant]:
        if self.chat_repo.find_private_chat(user_id=user_id) is not None:
            raise ValueError('Private chat already exists')
        chat = self.chat_repo.save(Chat.PrivateChatCreation())
        participant = self.participant_repo.save(Participant.Creation(chat_id=chat.id, user_id=user_id))
        return chat, participant

    def send_message(self, chat_id: int, sender_id: int, content: str) -> Message:
        participant = self.participant_repo.get_one(chat_id=chat_id, user_id=sender_id)
        message = self.message_repo.save(Message.Creation(chat_id=chat_id, participant_id=participant.id, content=content))
        return message
