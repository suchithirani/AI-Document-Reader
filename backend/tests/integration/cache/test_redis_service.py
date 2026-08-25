from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.redis import RedisClient


@pytest.mark.asyncio
async def test_redis_client_operations():
    client = RedisClient()
    mock_redis = MagicMock()

    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value="cached_val")
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=1)
    mock_redis.incr = AsyncMock(return_value=2)
    mock_redis.expire = AsyncMock(return_value=True)

    client.client = mock_redis

    assert await client.ping() is True
    assert await client.get("key") == "cached_val"
    assert await client.set("key", "val", ex=60) is True
    assert await client.exists("key") == 1
    assert await client.increment("counter") == 2
    await client.delete("key")
    mock_redis.delete.assert_awaited_once_with("key")
