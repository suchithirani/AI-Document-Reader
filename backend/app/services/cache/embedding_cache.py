import hashlib

from app.services.cache.service import (
    CacheService,
)


class EmbeddingCache:

    PREFIX = "embedding"

    def __init__(self):

        self.cache = CacheService()

    def _key(
        self,
        question: str,
    ) -> str:

        question = question.strip().lower()

        return (
            f"{self.PREFIX}:"
            f"{hashlib.sha256(question.encode()).hexdigest()}"
        )

    async def get(
        self,
        question: str,
    ):

        key = self._key(question)

        value = await self.cache.get(key)

        print(
            f"Redis GET: {key} -> {'HIT' if value else 'MISS'}"
        )

        return value

    async def set(
        self,
        question: str,
        embedding: list[float],
    ):

        key = self._key(question)

        await self.cache.set(
            key=key,
            value=embedding,
        )

        print(f"Redis SET: {key}")