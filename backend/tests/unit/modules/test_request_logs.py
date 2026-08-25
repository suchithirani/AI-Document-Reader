import pytest

from app.modules.request_logs.repository import RequestLogRepository
from app.modules.request_logs.service import RequestLogService


@pytest.mark.asyncio
async def test_request_log_service_and_repository(mock_db):
    service = RequestLogService(mock_db)

    # 1. Log request
    log = await service.log_request(
        request_id="req-12345",
        user_id="user_123",
        method="POST",
        path="/api/v1/search",
        query_params={},
        status_code=200,
        success=True,
        error_message=None,
        response_time_ms=125.5,
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0",
        request_size=200,
        response_size=1500,
    )
    assert log is not None

    # 2. Get logs
    repo = RequestLogRepository(mock_db)
    all_logs = await repo.get_logs(skip=0, limit=10)
    assert len(all_logs) >= 1

    user_logs = await repo.get_user_logs(user_id="user_123", skip=0, limit=10)
    assert len(user_logs) >= 1
    assert user_logs[0].request_id == "req-12345"
