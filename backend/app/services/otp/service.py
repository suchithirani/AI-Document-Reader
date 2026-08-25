from app.core.config import settings
from app.core.redis import redis_client
from app.services.otp.generator import OtpGenerator
from app.services.otp.hasher import OtpHasher


class OtpService:

    def __init__(self):

        self.redis = redis_client
        self.otp_generator = OtpGenerator()
        self.otp_hasher = OtpHasher()

    def _key(
        self,
        identifier: str,
    ) -> str:

        return f"{settings.OTP_PREFIX}:{identifier}"

    def _cooldown_key(
            self,
            identifier: str,
        ) -> str:

            return (
                f"{settings.OTP_COOLDOWN}:{identifier}"
            )

    async def generate(
        self,
        identifier: str,
    ) -> str:

        otp = self.otp_generator.generate()

        hashed = self.otp_hasher.hash(
            otp,
        )

        await self.redis.set(
            key=self._key(identifier),
            value=hashed,
            ex=settings.OTP_TTL,
        )

        return otp

    async def verify_and_delete(
        self,
        identifier: str,
        otp: str,
    ) -> bool:

        valid = await self.verify(
            identifier,
            otp,
        )

        if not valid:
            return False

        await self.delete(
            identifier,
        )

        return True

    async def can_resend(
        self,
        identifier: str,
    ) -> bool:

        return await self.redis.set_if_not_exists(
            key=self._cooldown_key(
                identifier,
            ),
            value="1",
            ex=settings.OTP_COOLDOWN,
        )

    async def resend_after(
        self,
        identifier: str,
    ) -> int:

        ttl = await self.redis.ttl(
            self._cooldown_key(
                identifier,
            )
        )

        return max(
            ttl,
            0,
        )

    async def verify(
        self,
        identifier: str,
        otp: str,
    ) -> bool:

        stored = await self.redis.get(
            self._key(identifier),
        )

        if stored is None:
            return False

        return (
            stored
            == self.otp_hasher.hash(
                otp,
            )
        )

    async def delete(
        self,
        identifier: str,
    ):

        await self.redis.delete(
            self._key(identifier),
        )
