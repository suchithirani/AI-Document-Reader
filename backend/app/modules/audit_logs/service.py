from app.common.utils.datetime import utc_now
from app.modules.audit_logs.repository import AuditLogRepository


class AuditLogService:

    def __init__(self, db):
        self.repository = AuditLogRepository(db)

    async def create_log(
        self,
        *,
        user_id: str | None,
        action: str,
        resource: str,
        resource_id: str | None = None,
        description: str,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):

        return await self.repository.create_log(
            {
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "resource_id": resource_id,
                "description": description,
                "metadata": metadata or {},
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": utc_now(),
            }
        )
