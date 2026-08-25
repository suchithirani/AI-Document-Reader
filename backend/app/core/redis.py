from redis.asyncio import Redis

from app.core.config import settings


class RedisClient:

    def __init__(self):

        self.client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )

    async def ping(self):
        return await self.client.ping()

    async def get(self, key: str):
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value,
        ex: int | None = None,
        nx: bool = False
    ):
        return await self.client.set(
            key,
            value,
            ex=ex,
            nx=nx
        )

    async def delete(
        self,
        key: str,
    ):
        await self.client.delete(key)

    async def exists(
        self,
        key: str,
    ):
        return await self.client.exists(key)

    async def increment(
        self,
        key: str,
    ):
        return await self.client.incr(key)

    async def expire(
        self,
        key: str,
        seconds: int,
    ):
        await self.client.expire(
            key,
            seconds,
        )

    async def close(self):
        await self.client.aclose()

    async def ttl(
        self,
        key: str,
    ):

        return await self.client.ttl(key)

    async def set_if_not_exists(
        self,
        key: str,
        value: str,
        ex: int,
    ):

        return await self.client.set(
            key,
            value,
            ex=ex,
            nx=True,
        )
redis_client = RedisClient()
