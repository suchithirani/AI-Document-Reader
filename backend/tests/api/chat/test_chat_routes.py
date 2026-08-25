from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.dependencies.service import get_chat_service
from app.main import app


def test_create_chat_session(test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user

    mock_service = AsyncMock()
    mock_service.create_session.return_value = {
        "session_id": "sess-123",
        "title": "New Chat",
        "document_ids": ["doc-1"],
    }
    app.dependency_overrides[get_chat_service] = lambda: mock_service

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat/sessions",
            json={"document_ids": ["doc-1"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["session_id"] == "sess-123"

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_chat_service, None)


def test_send_chat_message(test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user

    mock_service = AsyncMock()
    mock_service.send_message.return_value = {
        "answer": "This is a verified test response from the assistant. [1]",
        "sources": {
            "metadata": [],
            "content": [{"id": 1, "document_name": "test.pdf", "page_number": 1}]
        }
    }
    app.dependency_overrides[get_chat_service] = lambda: mock_service

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat/sessions/sess-123/messages",
            json={"question": "What is the summary?", "detail_level": "standard"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "This is a verified test response" in data["data"]["answer"]

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_chat_service, None)
