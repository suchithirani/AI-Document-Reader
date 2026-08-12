from app.common.exceptions.auth import (
    UnauthorizedException,
)
from app.core.redis import redis_client
from app.core.config import settings

class AuthLockoutService:

    MAX_ATTEMPTS = settings.LOGIN_MAX_ATTEMPTS

    LOCK_DURATION = settings.LOGIN_LOCK_DURATION

    async def is_locked(
        self,
        identifier: str,
    ) -> bool:

        key = f"login_lock:{identifier}"

        return bool(
            await redis_client.exists(key)
        )

    async def record_failure(
        self,
        identifier: str,
    ):

        attempts_key = (
            f"login_attempts:{identifier}"
        )

        attempts = await redis_client.increment(
            attempts_key
        )

        if attempts == 1:

            await redis_client.expire(
                attempts_key,
                self.LOCK_DURATION,
            )

        if attempts >= self.MAX_ATTEMPTS:

            lock_key = (
                f"login_lock:{identifier}"
            )

            await redis_client.set(
                key=lock_key,
                value="locked",
                ex=self.LOCK_DURATION,
            )

            raise UnauthorizedException(
                "Account temporarily locked. Try again in 10 minutes."
            )

    async def reset_failures(
        self,
        identifier: str,
    ):

        await redis_client.delete(
            f"login_attempts:{identifier}"
        )

        await redis_client.delete(
            f"login_lock:{identifier}"
        )