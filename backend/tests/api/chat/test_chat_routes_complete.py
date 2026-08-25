from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.dependencies.auth import get_current_user
from app.main import app


@pytest.mark.asyncio
async def test_chat_routes_full_suite(test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = create_access_token(str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create Session
        with patch("app.modules.chat.service.ChatService.create_session", new_callable=AsyncMock) as mock_create:
            mock_session = MagicMock(
                id="sess_123",
                owner_id=str(test_user.id),
                title="Test Session",
                model_dump=lambda **k: {"id": "sess_123", "owner_id": str(test_user.id), "title": "Test Session", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}
            )
            mock_create.return_value = mock_session

            res = await client.post(
                "/api/v1/chat/sessions",
                headers=headers,
                json={"document_ids": ["doc_123"]}
            )
            assert res.status_code == 200

        # 2. Get Sessions
        with patch("app.modules.chat.service.ChatService.get_sessions", new_callable=AsyncMock) as mock_get_sess:
            mock_get_sess.return_value = [mock_session]
            res = await client.get("/api/v1/chat/sessions", headers=headers)
            assert res.status_code == 200

        # 3. Rename Session
        with patch("app.modules.chat.service.ChatService.rename_session", new_callable=AsyncMock) as mock_rename:
            mock_rename.return_value = mock_session
            res = await client.patch(
                "/api/v1/chat/sessions/sess_123",
                headers=headers,
                json={"title": "Updated Title"}
            )
            assert res.status_code == 200

        # 4. Delete Session
        with patch("app.modules.chat.service.ChatService.delete_session", new_callable=AsyncMock) as mock_del:
            mock_del.return_value = {"message": "Deleted"}
            res = await client.delete("/api/v1/chat/sessions/sess_123", headers=headers)
            assert res.status_code == 200

        # 5. Send Message
        with patch("app.modules.chat.service.ChatService.send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {
                "answer": "RAG answer",
                "sources": {"metadata": [], "content": []}
            }
            res = await client.post(
                "/api/v1/chat/sessions/sess_123/messages",
                headers=headers,
                json={"question": "What is in doc?"}
            )
            assert res.status_code == 200

    app.dependency_overrides.clear()
