from core.repos.activity import AbstractActivityRepo


class UserActivityService:
    def __init__(self, activity_repo: AbstractActivityRepo):
        self.activity_repo = activity_repo

    def mark_participant_active(self, chat_id: int, participant_id: int) -> None:
        self.activity_repo.mark_participant_active(chat_id, participant_id)

    def unmark_participant_active(self, chat_id: int, participant_id: int) -> None:
        self.activity_repo.unmark_participant_active(chat_id, participant_id)

    def get_active_participant_ids(self, chat_id: int) -> set[int]:
        return self.activity_repo.get_active_participant_ids(chat_id)
