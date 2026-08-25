from app.workers.redis import (
    get_worker_redis,
)


class WorkerProcessingLockService:

    def __init__(self):

        self.redis = get_worker_redis()

    async def acquire(
        self,
        document_id: str,
        ttl: int = 600,
    ) -> bool:

        return await self.redis.set(
            f"processing:{document_id}",
            "1",
            ex=ttl,
            nx=True,
        )

    async def release(
        self,
        document_id: str,
    ):

        await self.redis.delete(
            f"processing:{document_id}"
        )

    async def is_processing(
        self,
        document_id: str,
    ) -> bool:

        return bool(
            await self.redis.exists(
                f"processing:{document_id}"
            )
        )

    async def close(self):

        await self.redis.aclose()
