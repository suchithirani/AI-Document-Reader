from unittest.mock import AsyncMock

import pytest

from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.service import AnalyticsService


@pytest.mark.asyncio
async def test_analytics_service_and_repository(mock_db):
    service = AnalyticsService(mock_db)

    # 1. Dashboard with mock repository returns
    service.repository.get_dashboard = AsyncMock(
        return_value={
            "total_ai_requests": 5,
            "prompt_tokens": 500,
            "completion_tokens": 100,
            "total_tokens": 600,
            "estimated_cost": 0.005,
            "average_latency": 150.0,
        }
    )
    service.repository.get_daily_usage = AsyncMock(return_value=[])
    service.repository.get_model_splits = AsyncMock(return_value=[])

    dashboard_res = await service.dashboard(days=7, owner_id="user_123")
    assert dashboard_res.total_ai_requests == 5
    assert dashboard_res.total_tokens == 600
    assert dashboard_res.average_latency_ms == 150.0

    # 2. Test create_ai_usage with all required model fields
    repo = AnalyticsRepository(mock_db)
    usage_entry = await repo.create_ai_usage({
        "user_id": "user_123",
        "provider": "gemini",
        "endpoint": "chat",
        "model": "gemini-2.5",
        "prompt_tokens": 150,
        "completion_tokens": 50,
        "total_tokens": 200,
        "latency_ms": 120.0,
        "estimated_cost": 0.002,
    })
    assert usage_entry is not None
