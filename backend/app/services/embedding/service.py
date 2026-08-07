from app.services.embedding.factory import (
    EmbeddingFactory,
)


class EmbeddingService:

    def __init__(
        self,
        provider: str,
    ):
        self.engine = (
            EmbeddingFactory.get_engine(
                provider
            )
        )

    async def create_embedding(
        self,
        text: str,
    ) -> list[float]:

        return await self.engine.create_embedding(
            text
        )