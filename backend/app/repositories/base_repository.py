from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection


class BaseRepository:
    """
    Base repository providing common CRUD operations.
    """

    def __init__(self, collection: AsyncCollection):
        self.collection = collection

    def _serialize_document(
        self,
        document: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """
        Convert MongoDB ObjectId to string.
        """
        if document is None:
            return None

        document = document.copy()

        if "_id" in document and isinstance(document["_id"], ObjectId):
            document["_id"] = str(document["_id"])

        return document

    async def create(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        result = await self.collection.insert_one(data)

        return await self.get_by_id(str(result.inserted_id))

    async def get_by_id(
        self,
        document_id: str,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(document_id):
            return None

        document = await self.collection.find_one(
            {"_id": ObjectId(document_id)}
        )

        return self._serialize_document(document)

    async def get_one(
        self,
        filters: dict[str, Any],
    ) -> dict[str, Any] | None:
        document = await self.collection.find_one(filters)

        return self._serialize_document(document)

    async def get_many(
        self,
        filters: dict[str, Any] | None = None,
        skip: int = 0,
        limit: int = 10,
        sort: list[tuple[str, int]] | None = None,
    ) -> list[dict[str, Any]]:
        filters = filters or {}

        cursor = self.collection.find(filters)

        if sort:
            cursor = cursor.sort(sort)

        cursor = cursor.skip(skip).limit(limit)

        documents = await cursor.to_list(length=limit)

        return [
            self._serialize_document(doc)
            for doc in documents
        ]

    async def update(
        self,
        document_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(document_id):
            return None

        document = await self.collection.find_one_and_update(
            {"_id": ObjectId(document_id)},
            {"$set": data},
            return_document=ReturnDocument.AFTER,
        )

        return self._serialize_document(document)

    async def delete(
        self,
        document_id: str,
    ) -> bool:
        if not ObjectId.is_valid(document_id):
            return False

        result = await self.collection.delete_one(
            {"_id": ObjectId(document_id)}
        )

        return result.deleted_count > 0

    async def count(
        self,
        filters: dict[str, Any] | None = None,
    ) -> int:
        return await self.collection.count_documents(filters or {})

    async def update_one(
        self,
        filters: dict[str, Any],
        data: dict[str, Any],
        ) -> dict[str, Any] | None:
        document = await self.collection.find_one_and_update(
            filters,
            {"$set": data},
            return_document=ReturnDocument.AFTER,
        )

        return self._serialize_document(document)

    async def update_many(
    self,
    filters: dict[str, Any],
    data: dict[str, Any],
    ):
        return await self.collection.update_many(
            filters,
            {"$set": data},
        )

    async def delete_many(
        self,
        filters: dict[str, Any],
    ) -> int:

        result = await self.collection.delete_many(
            filters
        )

        return result.deleted_count