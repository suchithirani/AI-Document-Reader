from app.common.constants import CollectionName, DocumentStatus
from app.common.utils.datetime import utc_now
from app.modules.documents.model import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(
            db[CollectionName.DOCUMENTS.value]
        )

    async def create_document(
        self,
        document: dict,
    ) -> Document:

        created = await self.create(document)

        return Document.model_validate(created)

    async def get_document_by_id(
        self,
        document_id: str,
    ) -> Document | None:

        document = await self.get_by_id(
        document_id
    )

        if document is None:
            return None

        return Document.model_validate(document)

    async def get_documents_by_owner(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Document]:

        documents = await self.get_many(
            filters={
                "owner_id": owner_id,
                "deleted_at": None,
            },
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)],
        )

        return [
            Document.model_validate(doc)
            for doc in documents
        ]

    async def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
    ) -> Document | None:

        document = await self.update(
            document_id,
            {
                "status": status,
                "updated_at": utc_now(),
            },
        )

        if document is None:
            return None

        return Document.model_validate(document)

    async def soft_delete(
        self,
        document_id: str,
    ) -> Document | None:

        document = await self.update(
            document_id,
            {
                "status": DocumentStatus.DELETED,
                "deleted_at": utc_now(),
                "updated_at": utc_now(),
            },
        )

        if document is None:
            return None

        return Document.model_validate(document)

    async def count_documents(
        self,
        owner_id: str,
    ) -> int:

        return await self.count(
            {
                "owner_id": owner_id,
                "deleted_at": None,
            }
        )