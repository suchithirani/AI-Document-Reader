from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.main import app


def test_auth_me_endpoint(test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user

    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "testuser@example.com"

    app.dependency_overrides.pop(get_current_user, None)


def test_auth_me_unauthorized():
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
