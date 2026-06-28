import json
from collections.abc import AsyncIterator
from typing import Any

from redis.asyncio import Redis as AsyncRedis

from core.eventbus.channels import Channels
from core.misc.redis import create_async_redis_client


class EventListener:
    async def listen_to(self, channel: str, handler: Any) -> None:
        ...

    async def listen(self) -> AsyncIterator[dict[str, Any]]:
        raise NotImplementedError()

    async def listen_once(self) -> dict[str, Any] | None:
        raise NotImplementedError()

    async def listen_forever(self) -> AsyncIterator[dict[str, Any]]:
        raise NotImplementedError()


class RedisEventListener(EventListener):
    def __init__(
        self,
        channel: Channels | str,
        redis_client: AsyncRedis | None = None,
        *,
        key_prefix: str = '',
        **channel_params: Any,
    ) -> None:
        super().__init__(channel, **channel_params)
        self.redis = redis_client or create_async_redis_client()
        self.key_prefix = key_prefix.strip(':')

    async def listen(self) -> AsyncIterator[dict[str, Any]]:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self._channel(self.channel_name()))
        try:
            async for message in pubsub.listen():
                if message.get('type') != 'message':
                    continue

                data = message.get('data')
                if isinstance(data, bytes):
                    data = data.decode()
                if not isinstance(data, str):
                    continue

                yield json.loads(data)
        finally:
            await pubsub.unsubscribe(self._channel(self.channel_name()))
            await pubsub.close()

    def _channel(self, key: str) -> str:
        if not self.key_prefix:
            return key
        return f'{self.key_prefix}:{key}'
