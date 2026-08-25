from unittest.mock import AsyncMock, patch

import pytest

from app.services.analytics.ai_usage import AIUsageService
from app.services.email.templates import EmailTemplates
from app.services.otp.generator import OtpGenerator
from app.services.otp.hasher import OtpHasher
from app.services.rate_limit.auth_lockout import AuthLockoutService


def test_otp_generator_and_hasher():
    otp = OtpGenerator.generate()
    assert len(otp) == 6
    assert otp.isdigit()

    hashed = OtpHasher.hash(otp)
    assert len(hashed) == 64
    assert OtpHasher.hash(otp) == hashed


def test_email_templates():
    verify_req = EmailTemplates.email_verification(email="test@example.com", otp="123456")
    assert "123456" in verify_req.body
    assert verify_req.to_email == "test@example.com"

    reset_req = EmailTemplates.forgot_password(email="test@example.com", otp="654321")
    assert "654321" in reset_req.body


@pytest.mark.asyncio
async def test_auth_lockout_service():
    lockout = AuthLockoutService()
    with patch("app.services.rate_limit.auth_lockout.redis_client.exists", new_callable=AsyncMock) as mock_exists:
        mock_exists.return_value = False
        is_locked = await lockout.is_locked("test@example.com")
        assert is_locked is False


@pytest.mark.asyncio
async def test_ai_usage_service(mock_db):
    usage_service = AIUsageService(db=mock_db)
    await usage_service.log(
        user_id="user_123",
        session_id="session_123",
        document_id="doc_123",
        endpoint="/api/v1/search",
        prompt_tokens=100,
        completion_tokens=50,
        latency_ms=250.0,
    )
    count = await mock_db["ai_usage_logs"].count_documents({})
    assert count == 1
