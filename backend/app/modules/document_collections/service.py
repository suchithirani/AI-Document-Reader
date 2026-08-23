import logging
from datetime import UTC, datetime
from app.common.exceptions.auth import (
    ForbiddenException,
    NotFoundException,
)
from app.modules.document_collections.model import DocumentCollection
from app.modules.document_collections.repository import DocumentCollectionRepository
from app.modules.documents.repository import DocumentRepository

logger = logging.getLogger(__name__)

class DocumentCollectionService:

    def __init__(self, db):
        self.repository = DocumentCollectionRepository(db)
        self.document_repository = DocumentRepository(db)

    async def create_collection(
        self,
        owner_id: str,
        name: str,
        description: str | None,
        document_ids: list[str],
    ) -> DocumentCollection:
        # Validate that all documents exist and are owned by this user
        for doc_id in document_ids:
            doc = await self.document_repository.get_document_by_id(doc_id)
            if doc is None:
                raise NotFoundException(f"Document {doc_id} not found.")
            if doc.owner_id != owner_id:
                raise ForbiddenException(f"Access to document {doc_id} is denied.")

        collection_dict = {
            "owner_id": owner_id,
            "name": name,
            "description": description,
            "document_ids": document_ids,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }

        return await self.repository.create_collection(collection_dict)

    async def get_collections(
        self,
        owner_id: str,
    ) -> list[DocumentCollection]:
        return await self.repository.get_collections(owner_id)

    async def get_collection(
        self,
        owner_id: str,
        collection_id: str,
    ) -> DocumentCollection:
        collection = await self.repository.get_collection(collection_id)
        if collection is None:
            raise NotFoundException("Collection not found.")
        if collection.owner_id != owner_id:
            raise ForbiddenException("Access to this collection is denied.")
        return collection

    async def update_collection(
        self,
        owner_id: str,
        collection_id: str,
        name: str | None,
        description: str | None,
        document_ids: list[str] | None,
    ) -> DocumentCollection:
        collection = await self.get_collection(owner_id, collection_id)

        update_dict = {}
        if name is not None:
            update_dict["name"] = name
        if description is not None:
            update_dict["description"] = description
        if document_ids is not None:
            # Validate document ownership
            for doc_id in document_ids:
                doc = await self.document_repository.get_document_by_id(doc_id)
                if doc is None:
                    raise NotFoundException(f"Document {doc_id} not found.")
                if doc.owner_id != owner_id:
                    raise ForbiddenException(f"Access to document {doc_id} is denied.")
            update_dict["document_ids"] = document_ids

        if update_dict:
            update_dict["updated_at"] = datetime.now(UTC)
            updated = await self.repository.update(collection_id, update_dict)
            return DocumentCollection.model_validate(updated)

        return collection

    async def delete_collection(
        self,
        owner_id: str,
        collection_id: str,
    ):
        await self.get_collection(owner_id, collection_id)
        await self.repository.update(
            collection_id,
            {"deleted_at": datetime.now(UTC)}
        )
