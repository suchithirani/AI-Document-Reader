from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.chat_summary_task import run_summary
from app.workers.chat_tasks import run_generate_title
from app.workers.cleanup_tasks import (
    cleanup_audit_logs_job,
    cleanup_refresh_tokens_job,
    cleanup_unreferenced_uploads_job,
)


@pytest.mark.asyncio
async def test_cleanup_tasks_jobs(mock_db):
    with patch("app.workers.cleanup_tasks.RefreshTokenRepository") as MockRefreshRepo, \
         patch("app.workers.cleanup_tasks.AuditLogRepository") as MockAuditRepo:

        mock_refresh = MagicMock()
        mock_refresh.delete_expired_tokens = AsyncMock(return_value=5)
        MockRefreshRepo.return_value = mock_refresh

        await cleanup_refresh_tokens_job(mock_db)
        assert mock_refresh.delete_expired_tokens.called

        mock_audit = MagicMock()
        mock_audit.delete_old_logs = AsyncMock(return_value=12)
        MockAuditRepo.return_value = mock_audit

        await cleanup_audit_logs_job(mock_db)
        assert mock_audit.delete_old_logs.called

        await cleanup_unreferenced_uploads_job(mock_db)


@pytest.mark.asyncio
async def test_chat_worker_jobs():
    with patch("app.workers.chat_summary_task.get_worker_database") as mock_get_db, \
         patch("app.workers.chat_summary_task.ChatSummaryService") as MockSummaryService:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_get_db.return_value = (mock_client, MagicMock())

        mock_summary = MagicMock()
        mock_summary.generate_summary = AsyncMock(return_value="Chat summary text")
        MockSummaryService.return_value = mock_summary

        await run_summary(session_id="s1")
        assert mock_summary.generate_summary.called

    with patch("app.workers.chat_tasks.get_worker_database") as mock_get_db, \
         patch("app.workers.chat_tasks.ChatTitleService") as MockTitleService:
        mock_get_db.return_value = (MagicMock(), MagicMock())

        mock_title = MagicMock()
        mock_title.generate_title = AsyncMock(return_value="New Title")
        MockTitleService.return_value = mock_title

        await run_generate_title(session_id="s1", question="What is AI?", answer="AI is...")
        assert mock_title.generate_title.called
