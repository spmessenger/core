from datetime import UTC, datetime
import re
from urllib.parse import urlparse, parse_qs
from uuid import uuid4

from core.entities import Chat, ChatType, Participant, Message
from core.entities.chat_group import ChatGroup
from core.entities.participant import DEFAULT_PIN_POSITION, PRIVATE_CHAT_PIN_POSITION
from core.entities.reply import Reply
from core.misc.utils.general import id_by_pair
from core.repos.abc import AbstractChatRepo, AbstractChatGroupRepo, AbstractParticipantRepo, AbstractUserRepo, AbstractMessageRepo
from core.services.activity import UserActivityService
from core.services.notifier import MessengerNotifier
from core.uow.messenger import MessengerUnitOfWork, MessengerUoWFactory


class MessengerService:
    _URL_REGEX = re.compile(r'((?:https?://|www\.)[^\s<]+)', re.IGNORECASE)

    def __init__(
        self,
        chat_repo: AbstractChatRepo,
        participant_repo: AbstractParticipantRepo,
        message_repo: AbstractMessageRepo,
        user_repo: AbstractUserRepo,
        chat_group_repo: AbstractChatGroupRepo | None = None,
        uow_factory: MessengerUoWFactory | None = None,
        activity_service: UserActivityService | None = None,
        notifier: MessengerNotifier | None = None,
    ):
        self.chat_repo = chat_repo
        self.participant_repo = participant_repo
        self.message_repo = message_repo
        self.user_repo = user_repo
        self.chat_group_repo = chat_group_repo
        self.uow_factory = uow_factory
        self.activity_service = activity_service
        self.notifier = notifier

    def _ensure_chat_group_repo(self) -> AbstractChatGroupRepo:
        if self.chat_group_repo is None:
            raise ValueError('Chat group repository is not configured')
        return self.chat_group_repo

    def get_chat_participant(self, chat_id: int, user_id: int) -> Participant:
        return self.participant_repo.get_one(chat_id=chat_id, user_id=user_id)

    def get_chat_participants(self, chat_id: int) -> list[Participant]:
        return self.participant_repo.find_all(chat_id=chat_id)

    def get_chat_messages(self, chat_id: int, user_id: int) -> tuple[Participant, list[Message]]:
        participant = self.get_chat_participant(
            chat_id=chat_id, user_id=user_id)
        messages = self.message_repo.find_all(chat_id=chat_id)
        self.participant_repo.reset_unread_messages_count(
            chat_id=chat_id, user_id=user_id)
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
        participant = self.get_chat_participant(
            chat_id=chat_id, user_id=user_id)
        self.participant_repo.reset_unread_messages_count(
            chat_id=chat_id, user_id=user_id)
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
            raise ValueError(
                'You cannot create dialog with user_id=participant_id')
        dialog = self.chat_repo.find_dialog(
            user_id=user_id, participant_id=participant_id)
        if dialog is not None:
            return dialog, self.participant_repo.update_chat_visible_to_all(chat_id=dialog.id, visible=True)

        chat = self.chat_repo.save(Chat.DialogCreation())
        participants = [
            self.participant_repo.save(Participant.MemberCreation(
                chat_id=chat.id, user_id=user_id)),
            self.participant_repo.save(Participant.MemberCreation(
                chat_id=chat.id, user_id=participant_id, chat_visible=False)),
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

        chat = self.chat_repo.save(Chat.GroupChatCreation(
            title=title, avatar_url=avatar_url))
        chat_participants = [
            self.participant_repo.save(
                Participant.MemberCreation(
                    chat_id=chat.id, user_id=participant_id)
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

    def send_message(
        self,
        chat_id: int,
        sender_id: int,
        content: str,
        reference_message_id: int | None = None,
        forwarded_from_message_id: int | None = None,
        connected_user_ids: set[int] | None = None,
    ) -> Message:
        participant = self.participant_repo.get_one(
            chat_id=chat_id, user_id=sender_id)
        if reference_message_id is not None and forwarded_from_message_id is not None:
            raise ValueError(
                'message cannot be reply and forward at the same time')

        if reference_message_id is not None:
            return self.reply(
                chat_id=chat_id,
                sender_id=sender_id,
                content=content,
                reference_message_id=reference_message_id,
                connected_user_ids=connected_user_ids,
            )

        if forwarded_from_message_id is not None:
            return self.forward(
                chat_id=chat_id,
                sender_id=sender_id,
                content=content,
                forwarded_from_message_id=forwarded_from_message_id,
                connected_user_ids=connected_user_ids,
            )

        return self._save_message(
            chat_id=chat_id,
            sender_id=sender_id,
            content=content,
            participant=participant,
            connected_user_ids=connected_user_ids,
        )

    def reply(
        self,
        chat_id: int,
        sender_id: int,
        content: str,
        reference_message_id: int,
        connected_user_ids: set[int] | None = None,
    ) -> Message:
        participant = self.participant_repo.get_one(
            chat_id=chat_id, user_id=sender_id)
        reference_author: str | None = None
        reference_content: str | None = None

        reference_message = self.message_repo.get_one(id=reference_message_id)
        if reference_message.chat_id != chat_id:
            raise ValueError(
                'reference_message_id must belong to the same chat')

        # Resolve author via chat participants to avoid edge-case repo id lookup issues.
        chat_participants = self.participant_repo.find_all(chat_id=chat_id)
        reference_participant = next(
            (
                participant
                for participant in chat_participants
                if participant.id == reference_message.participant_id
            ),
            None,
        )
        if reference_participant is not None:
            reference_user = self.user_repo.find_one_by_id(
                reference_participant.user_id)
            if reference_user is not None:
                reference_author = reference_user.username
        reference_content = reference_message.content

        return self._save_message(
            chat_id=chat_id,
            sender_id=sender_id,
            content=content,
            participant=participant,
            reference_message_id=reference_message_id,
            reference_author=reference_author,
            reference_content=reference_content,
            connected_user_ids=connected_user_ids,
        )

    def forward(
        self,
        chat_id: int,
        sender_id: int,
        content: str,
        forwarded_from_message_id: int,
        connected_user_ids: set[int] | None = None,
    ) -> Message:
        participant = self.participant_repo.get_one(
            chat_id=chat_id, user_id=sender_id)
        forwarded_from_author: str | None = None
        forwarded_from_author_avatar_url: str | None = None
        forwarded_from_content: str | None = None

        source_message = self.message_repo.get_one(
            id=forwarded_from_message_id)
        source_participant = self.participant_repo.find_one(
            chat_id=source_message.chat_id,
            user_id=sender_id,
        )
        if source_participant is None:
            raise ValueError('cannot forward message from inaccessible chat')

        source_chat_participants = self.participant_repo.find_all(
            chat_id=source_message.chat_id)
        source_author_participant = next(
            (
                participant
                for participant in source_chat_participants
                if participant.id == source_message.participant_id
            ),
            None,
        )
        if source_author_participant is not None:
            source_author_user = self.user_repo.find_one_by_id(
                source_author_participant.user_id)
            if source_author_user is not None:
                forwarded_from_author = source_author_user.username
                forwarded_from_author_avatar_url = source_author_user.avatar_url
        forwarded_from_content = source_message.content

        return self._save_message(
            chat_id=chat_id,
            sender_id=sender_id,
            content=content,
            participant=participant,
            forwarded_from_message_id=forwarded_from_message_id,
            forwarded_from_author=forwarded_from_author,
            forwarded_from_author_avatar_url=forwarded_from_author_avatar_url,
            forwarded_from_content=forwarded_from_content,
            connected_user_ids=connected_user_ids,
        )

    def reply_new(
        self,
        chat_id: int,
        sender_id: int,
        content: str,
        reply_to_id: int,
    ):
        with self.uow_factory() as uow:
            reply_to_msg = uow.message_repo.get_one(id=reply_to_id)
            message, participants = self._save_msg_in_uow(
                uow, chat_id, sender_id, content)
            uow.reply_repo.save(
                Reply.Creation(
                    replying_msg_id=message.id,
                    reply_to_msg_id=reply_to_id
                )
            )
            message.reply_to = Message.ReplyTo.model_validate(
                reply_to_msg, from_attributes=True)
            uow.commit()

            self.notifier.notify_new_message(chat_id, message)
            for p in participants:
                self.notifier.notify_chat_update(
                    p.user_id,
                    Chat.EventUpdate(
                        unread_messages_count=p.unread_messages_count,
                        last_message=message.content,
                        last_message_at=datetime.fromtimestamp(
                            float(message.created_at_timestamp),
                            tz=UTC,
                        ).isoformat(),
                    )
                )
            return message

    def send_msg(
        self,
        chat_id: int,
        sender_id: int,
        content: str,
    ):
        with self.uow_factory() as uow:
            message, participants = self._save_msg_in_uow(
                uow, chat_id, sender_id, content)
            uow.commit()

        self.notifier.notify_new_message(chat_id, message)
        for p in participants:
            self.notifier.notify_chat_update(
                p.user_id,
                Chat.EventUpdate(
                    unread_messages_count=p.unread_messages_count,
                    last_message=message.content,
                    last_message_at=datetime.fromtimestamp(
                        float(message.created_at_timestamp),
                        tz=UTC,
                    ).isoformat(),
                )
            )
        return message

    def _save_msg_in_uow(
        self,
        uow: MessengerUnitOfWork,
        chat_id: int,
        sender_id: int,
        content: str
    ):
        participant = uow.participant_repo.get_one(
            chat_id=chat_id,
            user_id=sender_id
        )
        message = uow.message_repo.save(
            Message.Creation(
                content=content, chat_id=chat_id,
                participant_id=participant.id,
                metadata_=self._create_metadata(content),
            )
        )
        uow.chat_repo.update_last_message(chat_id, message.id)
        active_participant_ids = self.activity_service.get_active_participant_ids(
            chat_id)
        uow.participant_repo.increment_unread_messages_count(
            chat_id,
            excluded_participant_ids=active_participant_ids
        )
        participants = uow.participant_repo.find_all(chat_id=chat_id)
        return message, participants

    def _save_message(
        self,
        chat_id: int,
        sender_id: int,
        content: str,
        participant: Participant | None = None,
        reference_message_id: int | None = None,
        reference_author: str | None = None,
        reference_content: str | None = None,
        forwarded_from_message_id: int | None = None,
        forwarded_from_author: str | None = None,
        forwarded_from_author_avatar_url: str | None = None,
        forwarded_from_content: str | None = None,
        connected_user_ids: set[int] | None = None,
        metadata_: dict | None = None,
    ) -> Message:
        if participant is None:
            participant = self.participant_repo.get_one(
                chat_id=chat_id, user_id=sender_id)

        message = self.message_repo.save(
            Message.Creation(
                chat_id=chat_id,
                participant_id=participant.id,
                reference_message_id=reference_message_id,
                reference_author=reference_author,
                reference_content=reference_content,
                forwarded_from_message_id=forwarded_from_message_id,
                forwarded_from_author=forwarded_from_author,
                forwarded_from_author_avatar_url=forwarded_from_author_avatar_url,
                forwarded_from_content=forwarded_from_content,
                content=content,
                metadata_=self._create_metadata(content),
            )
        )
        self.chat_repo.update_last_message(chat_id, message.id)
        excluded_user_ids = set(connected_user_ids or set())
        excluded_user_ids.add(sender_id)
        self.participant_repo.increment_unread_messages_count(
            chat_id=chat_id,
            excluded_user_ids=excluded_user_ids,
        )
        self.post_message(message)
        return message

    def _create_metadata(self, content: str) -> dict:
        metadata = {}
        youtube_meta = self._create_metadata_youtube(content)
        if youtube_meta:
            metadata['youtube'] = youtube_meta
        return metadata

    def _create_metadata_youtube(self, content: str) -> dict | None:
        def extract_youtube_video_id(url_value: str) -> str | None:
            parsed = urlparse(url_value)
            host = parsed.hostname.lower().replace('www.', '') if parsed.hostname else ''
            if host == 'youtu.be':
                path_parts = [part for part in parsed.path.split('/') if part]
                return path_parts[0] if path_parts else None
            if host in {'youtube.com', 'm.youtube.com'}:
                if parsed.path == '/watch':
                    video_id = parse_qs(parsed.query).get('v', [None])[0]
                    return video_id or None
                path_parts = [part for part in parsed.path.split('/') if part]
                if len(path_parts) >= 2 and path_parts[0] in {'shorts', 'embed'}:
                    return path_parts[1]
            return None

        for match in self._URL_REGEX.finditer(content):
            raw_url = match.group(1)
            normalized_url = (
                raw_url
                if raw_url.startswith(('http://', 'https://'))
                else f'https://{raw_url}'
            )
            video_id = extract_youtube_video_id(normalized_url)
            if video_id is None:
                continue

            return {
                'room_id': uuid4().hex,
                'youtube_video_id': video_id,
            }

        return None

    def delete_message(
        self,
        chat_id: int,
        user_id: int,
        message_id: int,
    ) -> Message:
        participant = self.participant_repo.get_one(
            chat_id=chat_id, user_id=user_id)
        message = self.message_repo.get_one(id=message_id)
        if message.chat_id != chat_id:
            raise ValueError('message_id must belong to the same chat')
        if message.participant_id != participant.id:
            raise ValueError('You can delete only your own messages')

        deleted_message = self.message_repo.delete_one(id=message_id)
        chat_messages = self.message_repo.find_all(chat_id=chat_id)
        if chat_messages:
            self.chat_repo.update_last_message(
                chat_id=chat_id, message_id=chat_messages[-1].id)
        else:
            self.chat_repo.update_last_message(
                chat_id=chat_id, message_id=None)
        return deleted_message

    def pin_chat(self, chat_id: int, user_id: int) -> bool:
        pin_position = self.participant_repo.get_max_pin_position(user_id) + 1
        participant = self.participant_repo.get_one(
            chat_id=chat_id, user_id=user_id)
        upd_participant = self.participant_repo.update(
            Participant.Update(id=participant.id, pin_position=pin_position))
        return upd_participant.pin_position == pin_position

    def unpin_chat(self, chat_id: int, user_id: int) -> bool:
        participant = self.participant_repo.get_one(
            chat_id=chat_id, user_id=user_id)
        upd_participant = self.participant_repo.update(Participant.Update(
            id=participant.id, pin_position=DEFAULT_PIN_POSITION))
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
        allowed_chat_ids = {
            chat.id for chat in available_chats if chat.type != ChatType.PRIVATE}

        for group in groups:
            invalid_chat_ids = [
                chat_id for chat_id in group.chat_ids if chat_id not in allowed_chat_ids]
            if invalid_chat_ids:
                raise ValueError(
                    f'Group "{group.title}" has invalid chat ids: {invalid_chat_ids}'
                )

        return chat_group_repo.replace_all(user_id=user_id, groups=groups)

    def post_message(self, message: Message) -> None:
        chat = self.chat_repo.get_by_id(message.chat_id)
        if chat.type == ChatType.DIALOG:
            self.participant_repo.update_chat_visible_to_all(
                chat_id=chat.id, visible=True)
