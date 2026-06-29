import json
from collections.abc import Mapping
from typing import Any, Protocol

from redis import Redis

from core.misc.redis import create_redis_client


class EventPublisher(Protocol):
    def publish(self, key: str, payload: Mapping[str, Any]) -> None:
        raise NotImplementedError()


class RedisEventPublisher(EventPublisher):
    def __init__(
        self,
        redis_client: Redis | None = None,
        *,
        key_prefix: str = '',
    ) -> None:
        self.redis = redis_client or create_redis_client()
        self.key_prefix = key_prefix.strip(':')

    def publish(self, key: str, payload: Mapping[str, Any]) -> None:
        self.redis.publish(
            self._channel(key),
            json.dumps(dict(payload), separators=(',', ':')),
        )

    def pubsub(self):
        return self.redis.pubsub()

    def _channel(self, key: str) -> str:
        if not self.key_prefix:
            return key
        return f'{self.key_prefix}:{key}'
