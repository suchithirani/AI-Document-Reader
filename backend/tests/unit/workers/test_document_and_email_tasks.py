from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.base import with_database
from app.workers.document_tasks import run_documents_processing
from app.workers.email_tasks import run_send_email
from app.workers.signal import shutdown_worker


@pytest.mark.asyncio
async def test_run_documents_processing():
    with patch("app.workers.document_tasks.get_worker_database") as mock_get_db, \
         patch("app.workers.document_tasks.DocumentProcessingService") as MockProcService:

        mock_get_db.return_value = (MagicMock(), MagicMock())
        mock_service = MagicMock()
        mock_service.process_documents = AsyncMock(return_value=True)
        MockProcService.return_value = mock_service

        await run_documents_processing(owner_id="user_123", document_ids=["doc_123"])
        assert mock_service.process_documents.called


@pytest.mark.asyncio
async def test_run_send_email():
    with patch("app.workers.email_tasks.EmailService.send", new_callable=AsyncMock) as mock_send:
        email_data = {
            "to_email": "test@example.com",
            "subject": "Hello",
            "body": "Welcome",
        }
        await run_send_email(email_data)
        assert mock_send.called


@pytest.mark.asyncio
async def test_worker_with_database_and_signal():
    async def sample_callback(db):
        return "callback_result"

    with patch("app.workers.base.get_worker_database") as mock_get_db:
        mock_get_db.return_value = (MagicMock(), MagicMock())
        res = await with_database(sample_callback)
        assert res == "callback_result"

    # Test shutdown_worker without crashing
    shutdown_worker()
