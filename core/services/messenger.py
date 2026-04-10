from core.entities import Chat, ChatType, Participant, Message
from core.entities.chat_group import ChatGroup
from core.entities.participant import DEFAULT_PIN_POSITION, PRIVATE_CHAT_PIN_POSITION
from core.repos.abc import AbstractChatRepo, AbstractChatGroupRepo, AbstractParticipantRepo, AbstractUserRepo, AbstractMessageRepo


class MessengerService:
    def __init__(
        self,
        chat_repo: AbstractChatRepo,
        participant_repo: AbstractParticipantRepo,
        message_repo: AbstractMessageRepo,
        user_repo: AbstractUserRepo,
        chat_group_repo: AbstractChatGroupRepo | None = None,
    ):
        self.chat_repo = chat_repo
        self.participant_repo = participant_repo
        self.message_repo = message_repo
        self.user_repo = user_repo
        self.chat_group_repo = chat_group_repo

    def _ensure_chat_group_repo(self) -> AbstractChatGroupRepo:
        if self.chat_group_repo is None:
            raise ValueError('Chat group repository is not configured')
        return self.chat_group_repo

    def get_chat_participant(self, chat_id: int, user_id: int) -> Participant:
        return self.participant_repo.get_one(chat_id=chat_id, user_id=user_id)

    def get_chat_participants(self, chat_id: int) -> list[Participant]:
        return self.participant_repo.find_all(chat_id=chat_id)

    def get_chat_messages(self, chat_id: int, user_id: int) -> tuple[Participant, list[Message]]:
        participant = self.get_chat_participant(chat_id=chat_id, user_id=user_id)
        messages = self.message_repo.find_all(chat_id=chat_id)
        if messages:
            participant = self.participant_repo.update_last_read_message(
                chat_id=chat_id,
                user_id=user_id,
                last_read_message_id=messages[-1].id,
            )
        return participant, messages

    def get_chat_messages_page(
        self,
        chat_id: int,
        user_id: int,
        before_message_id: int | None = None,
        limit: int = 50,
    ) -> tuple[Participant, list[Message], bool]:
        participant = self.get_chat_participant(chat_id=chat_id, user_id=user_id)
        messages, has_more = self.message_repo.find_page(
            chat_id=chat_id,
            before_message_id=before_message_id,
            limit=limit,
        )
        if before_message_id is None and messages:
            participant = self.participant_repo.update_last_read_message(
                chat_id=chat_id,
                user_id=user_id,
                last_read_message_id=messages[-1].id,
            )
        return participant, messages, has_more

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

    def get_chat_groups(self, user_id: int) -> list[ChatGroup]:
        chat_group_repo = self._ensure_chat_group_repo()
        return chat_group_repo.find_all(user_id=user_id)

    def replace_chat_groups(
        self,
        user_id: int,
        groups: list[ChatGroup.Creation],
    ) -> list[ChatGroup]:
        chat_group_repo = self._ensure_chat_group_repo()

        available_chats = self.chat_repo.find_all(user_id=user_id)
        allowed_chat_ids = {chat.id for chat in available_chats if chat.type != ChatType.PRIVATE}

        for group in groups:
            invalid_chat_ids = [chat_id for chat_id in group.chat_ids if chat_id not in allowed_chat_ids]
            if invalid_chat_ids:
                raise ValueError(
                    f'Group "{group.title}" has invalid chat ids: {invalid_chat_ids}'
                )

        return chat_group_repo.replace_all(user_id=user_id, groups=groups)

    def post_message(self, message: Message) -> None:
        chat = self.chat_repo.get_by_id(message.chat_id)
        if chat.type == ChatType.DIALOG:
            self.participant_repo.update_chat_visible_to_all(chat_id=chat.id, visible=True)
