from core.entities import Chat, ChatType, Participant, Message
from core.entities.participant import DEFAULT_PIN_POSITION, PRIVATE_CHAT_PIN_POSITION
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

    def get_chat_participant(self, chat_id: int, user_id: int) -> Participant:
        return self.participant_repo.get_one(chat_id=chat_id, user_id=user_id)

    def get_chat_participants(self, chat_id: int) -> list[Participant]:
        return self.participant_repo.find_all(chat_id=chat_id)

    def get_chat_messages(self, chat_id: int, user_id: int) -> tuple[Participant, list[Message]]:
        participant = self.get_chat_participant(chat_id=chat_id, user_id=user_id)
        messages = self.message_repo.find_all(chat_id=chat_id)
        return participant, messages

    def create_dialog(self, user_id: int, participant_id: int) -> tuple[Chat, list[Participant]]:
        if user_id == participant_id:
            raise ValueError('You cannot create dialog with user_id=participant_id')
        dialog = self.chat_repo.find_dialog(user_id=user_id, participant_id=participant_id)
        if dialog is not None:
            return dialog, self.participant_repo.update_chat_visible_to_all(chat_id=dialog.id, visible=True)

        chat = self.chat_repo.save(Chat.DialogCreation())
        participants = [
            self.participant_repo.save(Participant.MemberCreation(chat_id=chat.id, user_id=user_id)),
            self.participant_repo.save(Participant.MemberCreation(chat_id=chat.id, user_id=participant_id, chat_visible=False)),
        ]
        return chat, participants

    def create_group_chat(
        self,
        user_id: int,
        title: str,
        participants: list[int],
        avatar_url: str | None = None,
    ) -> tuple[Chat, list[Participant]]:
        participants = list(filter(lambda p: p != user_id, participants))

        chat = self.chat_repo.save(Chat.GroupChatCreation(title=title, avatar_url=avatar_url))
        chat_participants = [
            self.participant_repo.save(
                Participant.MemberCreation(chat_id=chat.id, user_id=participant_id)
            )
            for participant_id in participants
        ]
        chat_participants.append(
            self.participant_repo.save(
                Participant.AdminCreation(chat_id=chat.id, user_id=user_id)
            )
        )
        return chat, chat_participants

    def create_private_chat(self, user_id: int) -> tuple[Chat, Participant]:
        if self.chat_repo.find_private_chat(user_id=user_id) is not None:
            raise ValueError('Private chat already exists')
        chat = self.chat_repo.save(Chat.PrivateChatCreation())
        participant = self.participant_repo.save(Participant.MemberCreation(
            chat_id=chat.id, user_id=user_id, pin_position=PRIVATE_CHAT_PIN_POSITION
        ))
        return chat, participant

    def send_message(self, chat_id: int, sender_id: int, content: str) -> Message:
        participant = self.participant_repo.get_one(chat_id=chat_id, user_id=sender_id)
        message = self.message_repo.save(Message.Creation(chat_id=chat_id, participant_id=participant.id, content=content))
        self.chat_repo.update_last_message(chat_id, message.id)
        self.post_message(message)
        return message

    def pin_chat(self, chat_id: int, user_id: int) -> bool:
        pin_position = self.participant_repo.get_max_pin_position(user_id) + 1
        participant = self.participant_repo.get_one(chat_id=chat_id, user_id=user_id)
        upd_participant = self.participant_repo.update(Participant.Update(id=participant.id, pin_position=pin_position))
        return upd_participant.pin_position == pin_position

    def unpin_chat(self, chat_id: int, user_id: int) -> bool:
        participant = self.participant_repo.get_one(chat_id=chat_id, user_id=user_id)
        upd_participant = self.participant_repo.update(Participant.Update(id=participant.id, pin_position=DEFAULT_PIN_POSITION))
        return upd_participant.pin_position == DEFAULT_PIN_POSITION

    def post_message(self, message: Message) -> None:
        chat = self.chat_repo.get_by_id(message.chat_id)
        if chat.type == ChatType.DIALOG:
            self.participant_repo.update_chat_visible_to_all(chat_id=chat.id, visible=True)
