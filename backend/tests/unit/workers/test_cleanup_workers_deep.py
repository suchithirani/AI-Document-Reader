from unittest.mock import patch

import pytest

from app.workers.cleanup_tasks import (
    cleanup_audit_logs_job,
    cleanup_refresh_tokens_job,
    cleanup_temp_files,
    cleanup_unreferenced_uploads_job,
)
from app.workers.signal import shutdown_worker


@pytest.mark.asyncio
async def test_cleanup_tasks_execution(mock_db):
    # 1. Cleanup refresh tokens
    await cleanup_refresh_tokens_job(mock_db)

    # 2. Cleanup audit logs
    await cleanup_audit_logs_job(mock_db)

    # 3. Cleanup unreferenced uploads
    await cleanup_unreferenced_uploads_job(mock_db)

    # 4. Cleanup temp files
    with patch("app.services.storage.cleanup_service.StorageCleanupService.cleanup_directory", return_value=3):
        cleanup_temp_files()


def test_signal_handlers_shutdown():
    with patch("app.workers.signal.get_worker_loop", return_value=None):
        shutdown_worker()
