from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_endpoint_returns_expected_payload() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Service is healthy"
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["database"]["status"] in {"connected", "disconnected"}
