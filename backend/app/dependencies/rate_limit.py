from fastapi import Depends, Request

from app.services.rate_limit.service import (
    RateLimitService,
)


def rate_limit(
    *,
    limit: int,
    window: int,
):

    async def dependency(
        request: Request,
    ):

        user = getattr(
            request.state,
            "user",
            None,
        )

        identifier = (
            str(user.id)
            if user
            else (
                request.client.host
                if request.client
                else "anonymous"
            )
        )

        key = (
            f"rate_limit:"
            f"{request.method}:"
            f"{request.url.path}:"
            f"{identifier}"
        )

        service = RateLimitService()

        await service.check(
            key=key,
            limit=limit,
            window=window,
        )

    return Depends(dependency)
