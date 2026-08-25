from datetime import timedelta

from app.common.constants import CollectionName
from app.common.utils.datetime import utc_now
from app.modules.audit_logs.model import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditLogRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(
            db[CollectionName.AUDIT_LOGS.value]
        )

    async def create_log(
        self,
        log: dict,
    ) -> AuditLog:

        created = await self.create(log)

        return AuditLog.model_validate(created)

    async def delete_old_logs(
        self,
        retention_days: int,
    ) -> int:
        cutoff = utc_now() - timedelta(
            days=retention_days,
        )

        result = await self.collection.delete_many(
            {
                "created_at": {
                    "$lt": cutoff,
                }
            }
        )

        return result.deleted_count
