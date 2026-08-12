from app.core.redis import redis_client

from app.common.exceptions.auth import (
    RateLimitException,
)


class RateLimitService:

    async def check(
        self,
        *,
        key: str,
        limit: int,
        window: int,
    ) -> None:

        requests = await redis_client.increment(key)

        if requests == 1:
            await redis_client.expire(
                key,
                window,
            )

        if requests > limit:
            raise RateLimitException(
                f"Rate limit exceeded. Maximum {limit} requests every {window} seconds."
            )