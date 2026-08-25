from app.common.utils.datetime import utc_now
from app.modules.document_contents.repository import (
    DocumentContentRepository,
)


class DocumentContentService:

    def __init__(self, db):
        self.repository = (
            DocumentContentRepository(db)
        )

    async def save_pages(
        self,
        document_id: str,
        pages: list[str],
    ):

        now = utc_now()

        for page_number, text in enumerate(
            pages,
            start=1,
        ):

            await self.repository.create_content(
                {
                    "document_id": document_id,
                    "page_number": page_number,
                    "text": text,
                    "created_at": now,
                    "updated_at": now,
                }
            )

    async def copy_pages(
        self,
        source_document_id: str,
        target_document_id: str,
    ):

        source_pages = (
            await self.repository.get_pages(
                source_document_id
            )
        )

        if not source_pages:
            return 0

        now = utc_now()

        for page in source_pages:

            await self.repository.create_content(
                {
                    "document_id": target_document_id,
                    "page_number": page["page_number"],
                    "text": page["text"],
                    "created_at": now,
                    "updated_at": now,
                }
            )

        return len(source_pages)

    async def delete_document_contents(
        self,
        document_id: str,
    ):

        await self.repository.delete_by_document(
            document_id
        )
