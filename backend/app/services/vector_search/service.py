import logging
from typing import Any

from app.repositories.qdrant_repository import QdrantRepository

logger = logging.getLogger(__name__)

class VectorSearchService:
    def __init__(self):
        self.qdrant_repo = QdrantRepository()
        self.MIN_SCORE = 0.6

    def search(
        self,
        query_embedding: list[float],
        owner_id: str,
        document_ids: list[str] = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Uses Qdrant to find the most similar chunks based on the embedding.
        Filters strictly by the user's owner_id and optionally document_ids.
        """
        results = self.qdrant_repo.search(
            query_embedding=query_embedding,
            owner_id=owner_id,
            document_ids=document_ids,
            top_k=top_k
        )

        from types import SimpleNamespace

        scored_chunks = []
        for result in results:
            scored_chunks.append(
                {
                    "score": result["score"],
                    "chunk": SimpleNamespace(**result["chunk"]),
                    "raw_payload": result["chunk"]
                }
            )

        return scored_chunks[:top_k * 3]
