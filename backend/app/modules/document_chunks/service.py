from app.common.utils.datetime import utc_now
from app.modules.document_chunks.repository import (
    DocumentChunkRepository,
)


class DocumentChunkService:

    def __init__(self, db):
        self.repository = (
            DocumentChunkRepository(db)
        )

    async def save_chunks(
        self,
        document_id: str,
        page_number: int,
        chunks: list[str],
    ):

        now = utc_now()

        for index, chunk in enumerate(
            chunks
        ):

            await self.repository.create_chunk(
                {
                    "document_id": document_id,
                    "page_number": page_number,
                    "chunk_index": index,
                    "text": chunk,
                    "token_count": len(
                        chunk.split()
                    ),

                    # ---------- Metadata ----------
                    "word_count": len(
                        chunk.split()
                    ),

                    "character_count": len(
                        chunk
                    ),

                    "has_numbers": any(
                        char.isdigit()
                        for char in chunk
                    ),

                    "has_table": (
                        "|" in chunk
                        or "\t" in chunk
                    ),

                    "has_email": (
                        "@" in chunk
                    ),

                    "has_url": (
                        "http://" in chunk
                        or "https://" in chunk
                        or "www." in chunk
                    ),

                    "embedding": None,
                    "created_at": now,
                    "updated_at": now,
                }
            )

    async def get_chunks(
        self,
        document_id: str,
    ):
        return await self.repository.get_document_chunks(
            document_id
        )

    async def update_embedding(
        self,
        document_id: str,
        page_number: int,
        chunk_index: int,
        embedding: list[float],
    ):

        await self.repository.update_embedding(
            document_id,
            page_number,
            chunk_index,
            embedding,
        )

    async def delete_chunks(
        self,
        document_id: str,
    ):
        await self.repository.delete_document_chunks(
            document_id
        )

    async def count_chunks(
        self,
        document_id: str,
    ):
        return await self.repository.count_chunks(
            document_id
        )

    async def get_chunks_with_embeddings(
        self,
        document_id: str,
    ):
        return await self.repository.get_chunks_with_embeddings(
            document_id
        )