import json
from typing import Any

from app.core.config import settings
from app.core.redis import redis_client


class CacheService:

    async def get(
        self,
        key: str,
    ) -> Any | None:

        value = await redis_client.get(key)

        if value is None:
            return None

        return json.loads(value)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ):

        await redis_client.set(
            key=key,
            value=json.dumps(value),
            ex=ttl or settings.REDIS_CACHE_TTL,
        )

    async def delete(
        self,
        key: str,
    ):

        await redis_client.delete(key)

    async def increment(
        self,
        key: str,
    ) -> int:

        return await redis_client.increment(key)
