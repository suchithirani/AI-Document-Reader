from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.exceptions.auth import (
    AccountLockedException,
    BadRequestException,
    ForbiddenException,
    UnauthorizedException,
)
from app.core.security import hash_password
from app.modules.auth.model import User
from app.modules.auth.schema import (
    LoginRequest,
    RegisterRequest,
)
from app.modules.auth.service import AuthService


@pytest.mark.asyncio
async def test_auth_service_register_duplicate(mock_db):
    service = AuthService(mock_db)
    service.user_repository.get_by_email = AsyncMock(return_value=MagicMock())

    req = RegisterRequest(name="Suchit", email="suchit@example.com", password="Password123!")
    mock_http_req = MagicMock()

    with pytest.raises(BadRequestException, match="Email already registered"):
        await service.register(mock_http_req, req)


@pytest.mark.asyncio
async def test_auth_service_login_edge_cases(mock_db):
    service = AuthService(mock_db)
    mock_http_req = MagicMock()

    # 1. Non-existent user
    service.user_repository.get_by_email = AsyncMock(return_value=None)
    with pytest.raises(UnauthorizedException, match="Invalid email or password"):
        await service.login(mock_http_req, LoginRequest(email="unknown@example.com", password="Password123!"))

    # 2. Unverified user
    unverified_user = User(
        _id="u1",
        name="Unverified",
        email="unverified@example.com",
        password_hash=hash_password("Password123!"),
        is_verified=False,
        is_active=True,
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )
    service.user_repository.get_by_email = AsyncMock(return_value=unverified_user)
    with pytest.raises(ForbiddenException, match="Please verify your email"):
        await service.login(mock_http_req, LoginRequest(email="unverified@example.com", password="Password123!"))

    # 3. Inactive user
    inactive_user = User(
        _id="u2",
        name="Inactive",
        email="inactive@example.com",
        password_hash=hash_password("Password123!"),
        is_verified=True,
        is_active=False,
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )
    service.user_repository.get_by_email = AsyncMock(return_value=inactive_user)
    with pytest.raises(UnauthorizedException, match="Account is inactive"):
        await service.login(mock_http_req, LoginRequest(email="inactive@example.com", password="Password123!"))

    # 4. Locked account
    verified_user = User(
        _id="u3",
        name="Verified",
        email="verified@example.com",
        password_hash=hash_password("Password123!"),
        is_verified=True,
        is_active=True,
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )
    service.user_repository.get_by_email = AsyncMock(return_value=verified_user)
    service.lockout.is_locked = AsyncMock(return_value=True)
    with pytest.raises(AccountLockedException):
        await service.login(mock_http_req, LoginRequest(email="verified@example.com", password="Password123!"))

    # 5. Wrong password
    service.lockout.is_locked = AsyncMock(return_value=False)
    service.lockout.record_failure = AsyncMock()
    with pytest.raises(UnauthorizedException, match="Invalid email or password"):
        await service.login(mock_http_req, LoginRequest(email="verified@example.com", password="WrongPassword!"))
    assert service.lockout.record_failure.called
