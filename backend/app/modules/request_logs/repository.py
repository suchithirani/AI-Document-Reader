from datetime import datetime

from app.common.constants import CollectionName
from app.modules.request_logs.model import RequestLog
from app.repositories.base_repository import BaseRepository


class RequestLogRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(
            db[CollectionName.REQUEST_LOGS.value]
        )

    async def create_log(
        self,
        log: dict,
    ) -> RequestLog:
        created = await self.create(log)
        return RequestLog.model_validate(created)

    async def get_by_request_id(
        self,
        request_id: str,
    ) -> RequestLog | None:

        document = await self.get_one(
            {"request_id": request_id}
        )

        if document is None:
            return None

        return RequestLog.model_validate(document)

    async def get_logs(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RequestLog]:

        documents = await self.get_many(
            skip=skip,
            limit=limit,
            sort=[("timestamp", -1)],
        )

        return [
            RequestLog.model_validate(doc)
            for doc in documents
        ]

    async def get_user_logs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RequestLog]:

        documents = await self.get_many(
            filters={"user_id": user_id},
            skip=skip,
            limit=limit,
            sort=[("timestamp", -1)],
        )

        return [
            RequestLog.model_validate(doc)
            for doc in documents
        ]

    async def count_logs(self) -> int:
        return await self.count()

    async def delete_before(
        self,
        before: datetime,
    ) -> int:

        result = await self.collection.delete_many(
            {
                "timestamp": {
                    "$lt": before
                }
            }
        )

        return result.deleted_count
