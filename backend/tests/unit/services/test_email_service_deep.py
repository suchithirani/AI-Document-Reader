from unittest.mock import AsyncMock, patch

import pytest

from app.common.exceptions.email import EmailException
from app.services.email.queue_service import EmailQueueService
from app.services.email.schema import EmailRequest
from app.services.email.service import EmailService


@pytest.mark.asyncio
async def test_email_service_send():
    service = EmailService()
    req = EmailRequest(to_email="test@example.com", subject="Test Subject", body="Test Body")

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None
        await service.send(req)
        assert mock_send.called

    with patch("aiosmtplib.send", side_effect=Exception("SMTP failure")):
        with pytest.raises(EmailException):
            await service.send(req)


@pytest.mark.asyncio
async def test_email_queue_service():
    with patch("app.services.email.queue_service.send_email_task.delay") as mock_delay:
        queue_svc = EmailQueueService()

        await queue_svc.send_welcome_email(username="Suchit", email="suchit@example.com")
        assert mock_delay.called

        await queue_svc.send_verification_email(email="suchit@example.com", otp="123456")
        assert mock_delay.called
