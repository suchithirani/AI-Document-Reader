from app.modules.document_images.repository import (
    DocumentImageRepository,
)
from app.services.storage.service import StorageService


class DocumentImageService:

    def __init__(self, db):

        self.repository = (
            DocumentImageRepository(db)
        )
        self.storage_service = (
            StorageService(db)
        )

    async def save_images(
        self,
        images: list[dict],
    ):

        saved = []

        for image in images:

            result = await self.repository.create(
                image
            )

            saved.append(result)

        return saved

    async def delete_document_images(
        self,
        document_id: str,
    ):

        return await self.repository.delete_by_document(
            document_id
        )

    async def get_images_for_documents(
        self,
        document_ids: list[str],
    ):
        return await self.repository.get_by_documents(
            document_ids
        )

    async def get_images_for_document_pages(
        self,
        document_id: str,
        page_numbers: list[int],
    ):
        return await self.repository.get_by_document_pages(
            document_id=document_id,
            page_numbers=page_numbers,
        )

    async def get_images_for_query(
        self,
        document_ids: list[str],
        page_numbers: dict[str, list[int]] | None = None,
        limit: int = 10,
    ):
        images = []

        if page_numbers:

            for document_id in document_ids:

                pages = page_numbers.get(
                    document_id,
                    [],
                )

                if not pages:
                    continue

                document_images = (
                    await self.repository
                    .get_by_document_pages(
                        document_id=document_id,
                        page_numbers=pages,
                    )
                )

                images.extend(
                    document_images
                )

        else:

            images = (
                await self.repository
                .get_by_documents(
                    document_ids
                )
            )

        return images[:limit]

    async def get_document_images(
        self,
        document_id: str,
    ):

        return await self.repository.get_by_document(
            document_id
        )

    async def load_image_bytes(
        self,
        image: dict,
    ) -> bytes:

        return await self.storage_service.read_bytes(
            image["storage_path"]
        )