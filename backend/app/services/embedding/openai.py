class OpenAIEmbedding:

    async def create_embedding(
        self,
        text: str,
    ) -> list[float]:

        raise NotImplementedError()