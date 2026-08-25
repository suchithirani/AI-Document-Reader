from app.common.constants import CollectionName
from app.repositories.base_repository import BaseRepository


class DocumentImageRepository(BaseRepository):

    def __init__(self, db):

        super().__init__(
            db[
                CollectionName.DOCUMENT_IMAGES.value
            ]
        )

    async def get_by_document(
        self,
        document_id: str,
    ):

        return await self.get_many(
            filters={
                "document_id": document_id,
            },
            sort=[
                ("page_number", 1),
                ("image_index", 1),
            ],
        )

    async def get_by_documents(
        self,
        document_ids: list[str],
    ):
        return await self.get_many(
            filters={
                "document_id": {
                    "$in": document_ids,
                }
            },
            sort=[
                ("document_id", 1),
                ("page_number", 1),
                ("image_index", 1),
            ],
            limit=1000,
        )

    async def get_by_document_pages(
        self,
        document_id: str,
        page_numbers: list[int],
    ):
        return await self.get_many(
            filters={
                "document_id": document_id,
                "page_number": {
                    "$in": page_numbers,
                },
            },
            sort=[
                ("page_number", 1),
                ("image_index", 1),
            ],
            limit=1000,
        )

    async def delete_by_document(
        self,
        document_id: str,
    ):

        return await self.delete_many(
            {
                "document_id": document_id,
            }
        )
