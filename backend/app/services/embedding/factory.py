from app.services.embedding.gemini import (
    GeminiEmbedding,
)
from app.services.embedding.openai import (
    OpenAIEmbedding,
)
from app.services.embedding.local import (
    LocalEmbedding,
)
from app.services.embedding.ollama import (
    OllamaEmbedding,
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

        if provider == "ollama":
            return OllamaEmbedding()

        raise ValueError(
            "Unsupported embedding provider."
        )