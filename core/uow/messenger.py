from __future__ import annotations
from core.repos import AbstractChatRepo, AbstractChatGroupRepo, AbstractParticipantRepo, AbstractUserRepo, AbstractMessageRepo
from db.session import AsyncSession, Session, AsyncSessionLocal, SessionLocal


class MessengerUoWFactory:
    def __init__(
        self,
        chat_repo_class: type[AbstractChatRepo],
        chat_group_repo_class: type[AbstractChatGroupRepo],
        participant_repo_class: type[AbstractParticipantRepo],
        user_repo_class: type[AbstractUserRepo],
        message_repo_class: type[AbstractMessageRepo],
    ):
        self.chat_repo_class = chat_repo_class
        self.chat_group_repo_class = chat_group_repo_class
        self.participant_repo_class = participant_repo_class
        self.user_repo_class = user_repo_class
        self.message_repo_class = message_repo_class

    def __call__(self) -> MessengerUnitOfWork:
        return MessengerUnitOfWork(
            self.chat_repo_class(auto_commit=False),
            self.chat_group_repo_class(auto_commit=False),
            self.participant_repo_class(auto_commit=False),
            self.user_repo_class(auto_commit=False),
            self.message_repo_class(auto_commit=False),
        )


class MessengerUnitOfWork:
    def __init__(
        self,
        chat_repo: AbstractChatRepo | None = None,
        chat_group_repo: AbstractChatGroupRepo | None = None,
        participant_repo: AbstractParticipantRepo | None = None,
        user_repo: AbstractUserRepo | None = None,
        message_repo: AbstractMessageRepo | None = None,
    ):
        self.chat_repo = chat_repo
        self.chat_group_repo = chat_group_repo
        self.participant_repo = participant_repo
        self.user_repo = user_repo
        self.message_repo = message_repo
        self._asession: AsyncSession | None = None
        self._session: Session | None = None

    async def acommit(self):
        await self._asession.commit()

    async def arollback(self):
        await self._asession.rollback()

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()

    def __enter__(self):
        self._session = SessionLocal()
        self.chat_repo._session = self._session
        self.chat_group_repo._session = self._session
        self.participant_repo._session = self._session
        self.user_repo._session = self._session
        self.message_repo._session = self._session
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()

    async def __aenter__(self):
        self._asession = AsyncSessionLocal()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._asession.close()
