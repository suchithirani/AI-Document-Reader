from app.services.embedding.gemini import (
    GeminiEmbedding,
)
from app.services.embedding.openai import (
    OpenAIEmbedding,
)
from app.services.embedding.local import (
    LocalEmbedding,
)


class EmbeddingFactory:

    @staticmethod
    def get_engine(
        provider: str,
    ):

        provider = provider.lower()

        if provider == "gemini":
            return GeminiEmbedding()

        if provider == "openai":
            return OpenAIEmbedding()

        if provider == "local":
            return LocalEmbedding()

        raise ValueError(
            "Unsupported embedding provider."
        )