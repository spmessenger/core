from enum import StrEnum


class Channels(StrEnum):
    CHAT = 'chat:{chat_id}'
    USER = 'user:{user_id}'

    def build(self, **kwargs) -> str:
        return self.value.format(**kwargs)
