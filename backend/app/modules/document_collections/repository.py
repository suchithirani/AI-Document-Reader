from app.common.constants import CollectionName
from app.modules.document_collections.model import DocumentCollection
from app.repositories.base_repository import BaseRepository


class DocumentCollectionRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(
            db[
                CollectionName.DOCUMENT_COLLECTIONS.value
            ]
        )

    async def create_collection(
        self,
        collection: dict,
    ) -> DocumentCollection:
        created = await self.create(collection)
        return DocumentCollection.model_validate(created)

    async def get_collection(
        self,
        collection_id: str,
    ) -> DocumentCollection | None:
        collection = await super().get_by_id(collection_id)
        if collection is None or collection.get("deleted_at") is not None:
            return None
        return DocumentCollection.model_validate(collection)

    async def get_collections(
        self,
        owner_id: str,
    ) -> list[DocumentCollection]:
        collections = await self.get_many(
            filters={
                "owner_id": owner_id,
                "deleted_at": None,
            },
            sort=[
                ("updated_at", -1),
            ],
            limit=100,
        )
        return [
            DocumentCollection.model_validate(col)
            for col in collections
        ]
