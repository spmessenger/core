from abc import ABC, abstractmethod
from typing import Protocol

from redis import Redis

from core.settings import get_settings


class AbstractActivityRepo(ABC):
    @abstractmethod
    def mark_participant_active(self, chat_id: int, participant_id: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def unmark_participant_active(self, chat_id: int, participant_id: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_active_participant_ids(self, chat_id: int) -> set[int]:
        raise NotImplementedError()


class RedisClient(Protocol):
    def sadd(self, name: str, *values: object) -> int:
        ...

    def srem(self, name: str, *values: object) -> int:
        ...

    def smembers(self, name: str) -> set[bytes | str | int]:
        ...

    def expire(self, name: str, time: int) -> bool:
        ...


def create_redis_client(redis_url: str | None = None) -> Redis:
    return Redis.from_url(
        redis_url or get_settings().REDIS_URL,
        decode_responses=True,
    )


class RedisActivityRepo(AbstractActivityRepo):
    def __init__(
        self,
        redis_client: RedisClient | None = None,
        *,
        key_prefix: str = '',
        active_ttl_seconds: int | None = None,
    ) -> None:
        self.redis = redis_client or create_redis_client()
        self.key_prefix = key_prefix.strip(':')
        self.active_ttl_seconds = active_ttl_seconds

    def mark_participant_active(self, chat_id: int, participant_id: int) -> None:
        key = self._active_participants_key(chat_id)
        self.redis.sadd(key, participant_id)
        if self.active_ttl_seconds is not None:
            self.redis.expire(key, self.active_ttl_seconds)

    def unmark_participant_active(self, chat_id: int, participant_id: int) -> None:
        self.redis.srem(self._active_participants_key(chat_id), participant_id)

    def get_active_participant_ids(self, chat_id: int) -> set[int]:
        return {
            self._parse_participant_id(value)
            for value in self.redis.smembers(self._active_participants_key(chat_id))
        }

    def _active_participants_key(self, chat_id: int) -> str:
        key = f'chat:{chat_id}:active_participants'
        if not self.key_prefix:
            return key
        return f'{self.key_prefix}:{key}'

    def _parse_participant_id(self, value: bytes | str | int) -> int:
        if isinstance(value, bytes):
            value = value.decode()
        return int(value)
