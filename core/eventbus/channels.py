from enum import StrEnum


class Channels(StrEnum):
    CHAT = 'chat:{chat_id}'

    def build(self, **kwargs) -> str:
        return self.value.format(**kwargs)
