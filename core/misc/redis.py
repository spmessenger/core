from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from core.settings import get_settings


def create_redis_client(redis_url: str | None = None) -> Redis:
    return Redis.from_url(
        redis_url or get_settings().REDIS_URL,
        decode_responses=True,
    )


def create_async_redis_client(redis_url: str | None = None) -> AsyncRedis:
    return AsyncRedis.from_url(
        redis_url or get_settings().REDIS_URL,
        decode_responses=True,
    )
