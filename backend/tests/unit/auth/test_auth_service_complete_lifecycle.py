from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.security import create_refresh_token, hash_password
from app.modules.auth.model import User
from app.modules.auth.schema import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendOtpRequest,
    VerifyOtpRequest,
)
from app.modules.auth.service import AuthService


@pytest.mark.asyncio
async def test_auth_service_full_lifecycle(mock_db, test_user):
    service = AuthService(mock_db)

    mock_req = MagicMock()
    mock_req.client.host = "127.0.0.1"
    mock_req.headers.get.return_value = "Mozilla/5.0"

    # 1. Register new user
    service.user_repository.get_by_email = AsyncMock(return_value=None)
    service.user_repository.create_user = AsyncMock(return_value=test_user)
    service.otp_service.generate = AsyncMock(return_value="123456")
    service.email_queue.send_verification_email = AsyncMock(return_value=True)

    reg_res = await service.register(
        http_request=mock_req,
        request=RegisterRequest(name="New User", email="new@example.com", password="Password123!"),
    )
    assert "Registration successful" in reg_res["message"]

    # 2. Login successful
    service.user_repository.get_by_email = AsyncMock(return_value=test_user)
    service.lockout.is_locked = AsyncMock(return_value=False)
    service.lockout.reset_failures = AsyncMock(return_value=True)
    service.user_repository.update_last_login = AsyncMock(return_value=True)
    service.refresh_repository.create_refresh_token = AsyncMock(return_value=True)

    login_res = await service.login(
        http_request=mock_req,
        request=LoginRequest(email="testuser@example.com", password="Password123!"),
    )
    assert login_res.access_token is not None
    assert login_res.refresh_token is not None

    # 3. Refresh Token
    mock_token_doc = MagicMock(user_id=str(test_user.id), revoked=False)
    service.refresh_repository.get_by_token_hash = AsyncMock(return_value=mock_token_doc)
    service.user_repository.get_by_id = AsyncMock(return_value=test_user)
    service.refresh_repository.revoke_refresh_token = AsyncMock(return_value=True)

    raw_refresh = create_refresh_token(str(test_user.id))
    ref_res = await service.refresh_token(
        http_request=mock_req,
        request=RefreshTokenRequest(refresh_token=raw_refresh),
    )
    assert ref_res.access_token is not None

    # 4. Verify Email
    unverified_user = User(
        _id="6a8b765d9a8f6b09441789a0",
        name="Test",
        email="unverified@example.com",
        password_hash=hash_password("Pass123!"),
        is_verified=False,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    service.user_repository.get_by_email = AsyncMock(return_value=unverified_user)
    service.otp_service.verify_and_delete = AsyncMock(return_value=True)
    service.user_repository.verify_email = AsyncMock(return_value=True)
    service.email_queue.send_welcome_email = AsyncMock(return_value=True)

    verify_res = await service.verify_email(
        http_request=mock_req,
        request=VerifyOtpRequest(identifier="unverified@example.com", otp="123456"),
    )
    assert verify_res.access_token is not None

    # 5. Resend verification OTP
    service.otp_service.can_resend = AsyncMock(return_value=True)
    resend_res = await service.resend_verification_otp(
        request=SendOtpRequest(identifier="unverified@example.com"),
    )
    assert "Verification OTP sent" in resend_res["message"]

    # 6. Forgot Password
    service.email_queue.send_forgot_password_email = AsyncMock(return_value=True)
    forgot_res = await service.forgot_password(
        request=ForgotPasswordRequest(identifier="testuser@example.com"),
    )
    assert "Password reset OTP sent" in forgot_res["message"]

    # 7. Reset Password
    service.otp_service.verify = AsyncMock(return_value=True)
    service.user_repository.update_password = AsyncMock(return_value=True)
    service.refresh_repository.revoke_all_user_tokens = AsyncMock(return_value=True)
    service.email_queue.send_password_changed_email = AsyncMock(return_value=True)

    reset_res = await service.reset_password(
        http_request=mock_req,
        request=ResetPasswordRequest(identifier="testuser@example.com", otp="123456", new_password="NewPassword999!"),
    )
    assert "Password changed successfully" in reset_res["message"]

    # 8. Logout
    service.refresh_repository.get_by_token_hash = AsyncMock(return_value=mock_token_doc)
    logout_res = await service.logout(
        http_request=mock_req,
        current_user=test_user,
        request=RefreshTokenRequest(refresh_token=raw_refresh),
    )
    assert "Logged out successfully" in logout_res["message"]
