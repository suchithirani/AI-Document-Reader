from app.common.constants import CollectionName
from app.modules.document_contents.model import (
    DocumentContent,
)
from app.repositories.base_repository import (
    BaseRepository,
)


class DocumentContentRepository(
    BaseRepository,
):

    def __init__(self, db):
        super().__init__(
            db[
                CollectionName.DOCUMENT_CONTENTS.value
            ]
        )

    async def create_content(
        self,
        content: dict,
    ) -> DocumentContent:

        created = await self.create(content)

        return DocumentContent.model_validate(
            created
        )

    async def get_pages(
        self,
        document_id: str,
    ):
        return await self.get_many(
            {
                "document_id": document_id,
            },
            skip=0,
            limit=10000,
            sort=[
                ("page_number", 1),
            ],
        )

    async def get_by_document(
        self,
        document_id: str,
    ) -> list[DocumentContent]:

        documents = await self.get_many(
            filters={
                "document_id": document_id,
            },
            sort=[
                (
                    "page_number",
                    1,
                )
            ],
        )

        return [
            DocumentContent.model_validate(doc)
            for doc in documents
        ]

    async def delete_by_document(
    self,
    document_id: str,
) -> int:

        result = await self.collection.delete_many(
            {
                "document_id": document_id,
            }
        )

        return result.deleted_count
