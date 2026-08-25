from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_expected_payload() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Health check successful."
    assert payload["data"]["status"] == "healthy"
    assert "application" in payload["data"]
    assert "version" in payload["data"]
