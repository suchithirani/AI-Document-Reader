from google import genai

from app.core.config import settings
from app.common.exceptions.ai import (
    EmbeddingException,
)


class GeminiEmbedding:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

    async def create_embedding(
        self,
        text: str,
    ) -> list[float]:

        try:

            response = (
                self.client.models.embed_content(
                    model=settings.EMBEDDING_MODEL,
                    contents=text,
                )
            )

            return response.embeddings[0].values

        except Exception as exception:

            raise EmbeddingException(
                str(exception)
            ) from exception
        
    async def create_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        try:

            print("\n========== EMBEDDING API DEBUG ==========")
            print("Texts received:", len(texts))

            response = self.client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=texts,
            )

            embeddings = [
                embedding.values
                for embedding in response.embeddings
            ]

            print("Embeddings returned:", len(embeddings))
            print("=========================================\n")

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