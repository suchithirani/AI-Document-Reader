from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.dependencies.service import get_analytics_service
from app.main import app


def test_analytics_dashboard_endpoint(test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user

    mock_service = AsyncMock()
    mock_service.dashboard.return_value = {
        "total_documents": 12,
        "total_pages": 48,
        "total_queries": 150,
        "ai_tokens_used": 25000,
    }
    app.dependency_overrides[get_analytics_service] = lambda: mock_service

    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard?days=7")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_documents"] == 12

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_analytics_service, None)
