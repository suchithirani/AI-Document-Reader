from redis.asyncio import Redis

from app.core.config import settings


def get_worker_redis():

    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )