from app.common.constants import CollectionName
from app.repositories.base_repository import BaseRepository


class ProcessedContentRepository(BaseRepository):

    def __init__(self, db):

        super().__init__(
            db[
                CollectionName.PROCESSED_DOCUMENT_CONTENT.value
            ]
        )

    async def get_by_hash(
        self,
        file_hash: str,
    ):

        return await self.get_one(
            {
                "file_hash": file_hash,
            }
        )
