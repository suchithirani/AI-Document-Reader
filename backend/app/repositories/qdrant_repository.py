import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

_qdrant_client = None

class QdrantRepository:
    def __init__(self):
        global _qdrant_client
        if _qdrant_client is None:
            if settings.QDRANT_URL:
                _qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            else:
                _qdrant_client = QdrantClient(path=settings.QDRANT_PATH)

        self.client = _qdrant_client

        self.collection_name = settings.QDRANT_COLLECTION_NAME + "_v2"
        self.vector_size = 768  # Size of embeddings for Nomic/Gemini

        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection '{self.collection_name}'")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                )
        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {e}")

    def upsert_chunks(self, chunks: list[Any], owner_id: str):
        """
        Takes a list of Chunk models (from MongoDB) and upserts them to Qdrant.
        """
        if not chunks:
            return

        points = []
        for chunk in chunks:
            if not chunk.embedding:
                continue

            payload = {
                "owner_id": owner_id,
                "document_id": chunk.document_id,
                "document_name": getattr(chunk, "document_name", ""),
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "mongo_id": str(chunk.id),
                "text": chunk.text,
            }

            # Use the string hex ID directly if Qdrant requires UUID or int.
            # We'll use a string UUID format or just auto-generate a UUID from mongo_id.
            import uuid
            # Ensure a valid UUID is created from the 24-char hex string of mongo_id
            point_id = str(uuid.UUID(chunk.id.zfill(32)))

            points.append(
                PointStruct(
                    id=point_id,
                    vector=chunk.embedding,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

    def search(self, query_embedding: list[float], owner_id: str, document_ids: list[str] = None, top_k: int = 5) -> list[dict]:
        """
        Searches Qdrant using the embedding, scoped strictly to the owner_id and optionally document_ids.
        """
        try:
            must_filters = [
                FieldCondition(
                    key="owner_id",
                    match=MatchValue(value=owner_id)
                )
            ]

            if document_ids:
                from qdrant_client.http.models import MatchAny
                must_filters.append(
                    FieldCondition(
                        key="document_id",
                        match=MatchAny(any=document_ids)
                    )
                )

            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                query_filter=Filter(
                    must=must_filters
                ),
                limit=top_k * 3,  # Fetch extra to match old logic and allow reranking
            )

            results = []
            for hit in search_result.points:
                results.append({
                    "score": hit.score,
                    "chunk": hit.payload,
                })

            return results
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []
