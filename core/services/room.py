from core.entities.room import YouTubeRoomModel
from core.repos.room import AbstractYouTubeRoomRepo
from core.misc.utils.general import id_by_pair


class YouTubeRoom:
    def __init__(self, repo: AbstractYouTubeRoomRepo):
        self.repo = repo

    def get_room(self, chat_id: int, message_id: int) -> YouTubeRoomModel:
        room_id = id_by_pair(chat_id, message_id)
        room = self.repo.find_by_id(room_id)
        if room is None:
            room = self.repo.create(YouTubeRoomModel.Creation(
                id=room_id, chat_id=chat_id, message_id=message_id))
        return YouTubeRoomModel(id=room.id, chat_id=room.chat_id, message_id=room.message_id)
