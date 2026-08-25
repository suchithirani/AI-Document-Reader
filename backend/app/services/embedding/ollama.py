import httpx

from app.common.exceptions.ai import (
    EmbeddingException,
)
from app.core.config import settings


class OllamaEmbedding:
    """Ollama provider for local embeddings."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_EMBEDDING_MODEL
        self.timeout = httpx.Timeout(120.0)

    async def create_embedding(
        self,
        text: str,
    ) -> list[float]:
        try:
            payload = {
                "model": self.model,
                "input": text,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json=payload,
                )

                if response.status_code != 200:
                    raise EmbeddingException(
                        f"Ollama returned status {response.status_code}: {response.text}"
                    )

                data = response.json()

            embeddings = data.get("embeddings", [])
            if not embeddings:
                raise EmbeddingException("No embeddings returned from Ollama.")

            return embeddings[0]

        except Exception as exception:
            raise EmbeddingException(
                str(exception)
            ) from exception

    async def create_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        try:
            print("\n========== OLLAMA EMBEDDING API DEBUG ==========")
            print("Texts received:", len(texts))

            payload = {
                "model": self.model,
                "input": texts,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json=payload,
                )

                if response.status_code != 200:
                    raise EmbeddingException(
                        f"Ollama returned status {response.status_code}: {response.text}"
                    )

                data = response.json()

            embeddings = data.get("embeddings", [])

            print("Embeddings returned:", len(embeddings))
            print("================================================\n")

            if len(embeddings) != len(texts):
                raise EmbeddingException(
                    f"Embedding count mismatch: "
                    f"{len(texts)} texts -> "
                    f"{len(embeddings)} embeddings"
                )

            return embeddings

        except Exception as exception:
            raise EmbeddingException(
                str(exception)
            ) from exception
