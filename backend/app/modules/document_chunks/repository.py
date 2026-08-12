from app.common.constants import CollectionName
from app.modules.document_chunks.model import (
    DocumentChunk,
)
from app.repositories.base_repository import (
    BaseRepository,
)
from app.modules.documents.repository import DocumentRepository


class DocumentChunkRepository(
    BaseRepository,
):

    def __init__(self, db):
        super().__init__(
            db[
                CollectionName.DOCUMENT_CHUNKS.value
            ]
        )
        self.document_repository = DocumentRepository(db)

    async def create_chunk(
        self,
        chunk: dict,
    ) -> DocumentChunk:

        created = await self.create(chunk)

        return DocumentChunk.model_validate(
            created
        )

    async def get_document_chunks(
        self,
        document_id: str,
    ) -> list[DocumentChunk]:

        chunks = await self.get_many(
            filters={
                "document_id": document_id,
            },
            sort=[
                ("page_number", 1),
                ("chunk_index", 1),
            ],
        )

        return [
            DocumentChunk.model_validate(
                chunk
            )
            for chunk in chunks
        ]

    async def update_embedding(
      
        self,
        document_id: str,
        page_number: int,
        chunk_index: int,
        embedding: list[float],
    ):

        await self.update_one(
            {
                "document_id": document_id,
                "page_number": page_number,
                "chunk_index": chunk_index,
            },
            {
                "embedding": embedding,
            },
        )
        
    async def delete_document_chunks(
        self,
        document_id: str,
    ) -> int:

        result = await self.collection.delete_many(
            {
                "document_id": document_id,
            }
        )

        return result.deleted_count

    async def count_chunks(
        self,
        document_id: str,
    ) -> int:

        return await self.count(
            {
                "document_id": document_id,
            }
        )

    async def get_chunks_for_document(
        self,
        document_id: str,
    ):

        return await self.get_many(
            {
                "document_id": document_id,
            },
            skip=0,
            limit=100000,
            sort=[
                ("page_number", 1),
                ("chunk_index", 1),
            ],
    )

    async def get_chunks_with_embeddings(
        self,
        document_ids: list[str],
    ):

        chunks = await self.get_many(
            filters={
                "document_id": {"$in": document_ids},
                "embedding": {
                    "$ne": None,
                },
            },
            sort=[
                ("page_number", 1),
                ("chunk_index", 1),
            ],
        )

        document_names = await self.document_repository.get_document_names(
            document_ids,
        )

        result = []

        for chunk in chunks:

            model = DocumentChunk.model_validate(chunk)

            model.document_name = document_names.get(
                model.document_id,
                "Unknown Document",
            )

            result.append(model)

        return result