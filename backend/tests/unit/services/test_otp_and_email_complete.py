from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.otp.service import OtpService


@pytest.mark.asyncio
async def test_otp_service_complete():
    mock_redis = MagicMock()
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.set_if_not_exists = AsyncMock(return_value=True)
    mock_redis.ttl = AsyncMock(return_value=45)

    service = OtpService()
    service.redis = mock_redis

    # 1. Generate
    otp = await service.generate("suchit@example.com")
    assert len(otp) == 6
    assert mock_redis.set.called

    # 2. Verify with missing OTP
    valid_missing = await service.verify("suchit@example.com", "123456")
    assert valid_missing is False

    # 3. Verify with matching OTP
    hashed = service.otp_hasher.hash("123456")
    mock_redis.get = AsyncMock(return_value=hashed)
    valid_match = await service.verify("suchit@example.com", "123456")
    assert valid_match is True

    # 4. Verify and delete
    verified_deleted = await service.verify_and_delete("suchit@example.com", "123456")
    assert verified_deleted is True
    assert mock_redis.delete.called

    # 5. Can resend & resend after
    can_res = await service.can_resend("suchit@example.com")
    assert can_res is True

    ttl = await service.resend_after("suchit@example.com")
    assert ttl == 45
