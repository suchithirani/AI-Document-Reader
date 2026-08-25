from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.process_lock import WorkerProcessingLockService


@pytest.mark.asyncio
async def test_worker_processing_lock_service():
    mock_redis = MagicMock()
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=1)
    mock_redis.aclose = AsyncMock(return_value=None)

    with patch("app.workers.process_lock.get_worker_redis", return_value=mock_redis):
        lock_service = WorkerProcessingLockService()

        acquired = await lock_service.acquire("doc-123", ttl=300)
        assert acquired is True
        mock_redis.set.assert_awaited_once_with("processing:doc-123", "1", ex=300, nx=True)

        is_proc = await lock_service.is_processing("doc-123")
        assert is_proc is True

        await lock_service.release("doc-123")
        mock_redis.delete.assert_awaited_once_with("processing:doc-123")

        await lock_service.close()
        mock_redis.aclose.assert_awaited_once()
