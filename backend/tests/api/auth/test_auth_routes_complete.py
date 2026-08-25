from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.dependencies.auth import get_current_user
from app.main import app


@pytest.mark.asyncio
async def test_auth_routes_full_suite(test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. Register Route - Validation error (invalid email)
        res = await client.post("/api/v1/auth/register", json={
            "name": "Short",
            "email": "not-an-email",
            "password": "123",
        })
        assert res.status_code == 422

        # 2. Register Route - Successful
        with patch("app.modules.auth.service.AuthService.register", new_callable=AsyncMock) as mock_reg:
            mock_reg.return_value = {"message": "Registration successful."}
            res = await client.post("/api/v1/auth/register", json={
                "name": "New User",
                "email": "valid@example.com",
                "password": "Password123!",
            })
            assert res.status_code == 201

        # 3. Forgot Password Route
        with patch("app.modules.auth.service.AuthService.forgot_password", new_callable=AsyncMock) as mock_fp:
            mock_fp.return_value = {"message": "OTP sent."}
            res = await client.post("/api/v1/auth/forgot-password", json={
                "identifier": "valid@example.com"
            })
            assert res.status_code == 200

        # 4. Reset Password Route
        with patch("app.modules.auth.service.AuthService.reset_password", new_callable=AsyncMock) as mock_rp:
            mock_rp.return_value = {"message": "Password reset successful."}
            res = await client.post("/api/v1/auth/reset-password", json={
                "identifier": "valid@example.com",
                "otp": "123456",
                "new_password": "NewPassword123!"
            })
            assert res.status_code == 200

        # 5. Logout Route
        token = create_access_token(str(test_user.id))
        with patch("app.modules.auth.service.AuthService.logout", new_callable=AsyncMock) as mock_out:
            mock_out.return_value = {"message": "Logged out."}
            res = await client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {token}"},
                json={"refresh_token": "refresh_val"}
            )
            assert res.status_code == 200

    app.dependency_overrides.clear()
