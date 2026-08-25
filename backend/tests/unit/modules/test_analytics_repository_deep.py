import pytest

from app.modules.analytics.repository import AnalyticsRepository


@pytest.mark.asyncio
async def test_analytics_repository_dashboard_and_breakdowns(mock_db):
    repo = AnalyticsRepository(mock_db)

    # 1. Create AI usage
    await repo.create_ai_usage({
        "user_id": "u1",
        "model": "gemini-2.5-flash",
        "provider": "gemini",
        "endpoint": "/api/v1/search",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "latency_ms": 120.0,
        "estimated_cost": 0.005,
    })

    # 2. Get dashboard
    dash = await repo.get_dashboard(days=7, owner_id="u1")
    assert dash is not None
    assert dash["total_tokens"] == 150

    # 3. Get daily usage
    daily = await repo.get_daily_usage(days=7, owner_id="u1")
    assert len(daily) >= 1

    # 4. Count endpoint
    count = await repo.count_endpoint(endpoint="/api/v1/search", days=7, owner_id="u1")
    assert isinstance(count, int)

    # 5. Get model splits
    splits = await repo.get_model_splits(days=7, owner_id="u1")
    assert isinstance(splits, list)
