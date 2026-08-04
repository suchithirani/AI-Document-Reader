from app.common.constants import CollectionName
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