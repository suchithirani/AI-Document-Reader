import hashlib

from app.services.cache.service import (
    CacheService,
)


class ResponseCache:

    PREFIX = "response"

    def __init__(self):

        self.cache = CacheService()

    def _key(
        self,
        key: str,
    ) -> str:

        return (
            f"{self.PREFIX}:"
            f"{hashlib.sha256(key.encode()).hexdigest()}"
        )

    def _version_key(
        self,
        key: str,
    ) -> str:

        return f"{self._key(key)}:version"

    async def _version(
        self,
        key: str,
    ) -> int:

        version = await self.cache.get(
            self._version_key(key)
        )

        return version or 0

    async def get(
        self,
        key: str,
    ):

        version = await self._version(key)

        return await self.cache.get(
            f"{self._key(key)}:{version}"
        )

    async def set(
        self,
        key: str,
        value,
        ttl: int | None = None,
    ):

        version = await self._version(key)

        await self.cache.set(
            key=f"{self._key(key)}:{version}",
            value=value,
            ttl=ttl,
        )

    async def delete(
        self,
        key: str,
    ):
        await self.cache.increment(
            self._version_key(key)
        )
