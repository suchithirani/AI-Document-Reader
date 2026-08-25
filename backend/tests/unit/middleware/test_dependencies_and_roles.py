from unittest.mock import MagicMock

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.common.constants import UserRole
from app.common.exceptions.auth import ForbiddenException, UnauthorizedException
from app.dependencies.auth import get_current_user
from app.dependencies.role import AdminOnly


@pytest.mark.asyncio
async def test_auth_dependency_missing_and_invalid_tokens(mock_db):
    mock_request = MagicMock()

    # 1. Invalid JWT token payload (not an access token)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.string")
    with pytest.raises(UnauthorizedException):
        await get_current_user(request=mock_request, credentials=creds, db=mock_db)


@pytest.mark.asyncio
async def test_role_dependency(test_user):
    # User is not admin -> 403 Forbidden
    test_user.role = UserRole.USER
    with pytest.raises(ForbiddenException):
        await AdminOnly(current_user=test_user)

    # User is admin -> allowed
    test_user.role = UserRole.ADMIN
    res = await AdminOnly(current_user=test_user)
    assert res.role == UserRole.ADMIN
