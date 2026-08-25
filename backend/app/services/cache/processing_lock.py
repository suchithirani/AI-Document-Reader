from app.core.redis import redis_client


class ProcessingLockService:


    async def acquire(
        self,
        document_id: str,
        ttl: int = 600,
    ) -> bool:

        return await redis_client.set(
            key=f"processing:{document_id}",
            value="1",
            ex=ttl,
            nx=True,
        )

    async def release(
        self,
        document_id: str,
    ):

        await redis_client.delete(
            f"processing:{document_id}"
        )

    async def is_processing(
        self,
        document_id: str,
    ) -> bool:

        return bool(
            await redis_client.exists(
                f"processing:{document_id}"
            )
        )
