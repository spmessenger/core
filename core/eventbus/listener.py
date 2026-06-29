import json
from typing import Any

from redis.asyncio import Redis as AsyncRedis

from core.eventbus.channels import Channels
from core.misc.redis import create_async_redis_client


class EventListener:
    async def wait_for_event(self) -> dict[str, Any]:
        raise NotImplementedError()

    async def listen(self) -> None:
        raise NotImplementedError()

    async def close(self) -> None:
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
        self.redis = redis_client or create_async_redis_client()
        self._owns_redis_client = redis_client is None
        self.key_prefix = key_prefix.strip(':')
        if isinstance(channel, Channels):
            channel_key = channel.build(**channel_params)
        else:
            channel_key = channel.format(**channel_params)
        self.channel = self._channel(channel_key)
        self.pubsub = self.redis.pubsub()
        self._subscribed = False

    async def listen(self) -> None:
        await self.pubsub.subscribe(self.channel)
        self._subscribed = True

    async def wait_for_event(self) -> dict[str, Any]:
        if not self._subscribed:
            await self.listen()

        async for message in self.pubsub.listen():
            if message.get('type') != 'message':
                continue

            data = message.get('data')
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            if isinstance(data, str):
                return json.loads(data)
            if isinstance(data, dict):
                return data

            raise ValueError(f'Unsupported event payload type: {type(data)!r}')

        raise RuntimeError('Redis pubsub listener stopped')

    async def close(self) -> None:
        try:
            if self._subscribed:
                await self.pubsub.unsubscribe(self.channel)
        finally:
            await self.pubsub.aclose()
            if self._owns_redis_client:
                await self.redis.aclose()

    def _channel(self, key: str) -> str:
        if not self.key_prefix:
            return key
        return f'{self.key_prefix}:{key}'
