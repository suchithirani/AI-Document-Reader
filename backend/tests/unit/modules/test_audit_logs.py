import pytest

from app.common.constants import AuditAction, AuditResource
from app.modules.audit_logs.repository import AuditLogRepository
from app.modules.audit_logs.service import AuditLogService


@pytest.mark.asyncio
async def test_audit_log_service_and_repository(mock_db):
    service = AuditLogService(mock_db)

    # 1. Create log
    log_entry = await service.create_log(
        user_id="user_123",
        action=AuditAction.DOCUMENT_UPLOAD,
        resource=AuditResource.DOCUMENT,
        resource_id="doc_123",
        description="User uploaded file test.pdf",
        metadata={"filename": "test.pdf"},
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0",
    )
    assert log_entry is not None

    # 2. Delete old logs via repository
    repo = AuditLogRepository(mock_db)
    deleted = await repo.delete_old_logs(retention_days=0)
    assert deleted >= 0
