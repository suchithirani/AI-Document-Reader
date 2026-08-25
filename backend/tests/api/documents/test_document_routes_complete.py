from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.common.constants import DocumentStatus
from app.core.security import create_access_token
from app.dependencies.auth import get_current_user
from app.main import app
from app.modules.documents.model import Document


@pytest.mark.asyncio
async def test_document_routes_full_suite(test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = create_access_token(str(test_user.id))
        headers = {"Authorization": f"Bearer {token}"}

        now = datetime.now(UTC)
        doc = Document(
            id=str(ObjectId()),
            owner_id=str(test_user.id),
            original_filename="sample.pdf",
            filename="123_sample.pdf",
            storage_provider="local",
            storage_path="uploads/123_sample.pdf",
            mime_type="application/pdf",
            extension=".pdf",
            file_size=1024,
            version=1,
            version_group_id="vg1",
            is_latest=True,
            status=DocumentStatus.READY,
            progress=100,
            created_at=now,
            updated_at=now,
        )

        # 1. Get Documents
        with patch("app.modules.documents.service.DocumentService.get_documents", new_callable=AsyncMock) as mock_get, \
             patch("app.modules.documents.service.DocumentService.count_documents", new_callable=AsyncMock) as mock_cnt:
            mock_get.return_value = [doc]
            mock_cnt.return_value = 1
            res = await client.get("/api/v1/documents", headers=headers)
            assert res.status_code == 200

        # 2. Get Document by ID
        with patch("app.modules.documents.service.DocumentService.get_document", new_callable=AsyncMock) as mock_get_one:
            mock_get_one.return_value = doc
            res = await client.get(f"/api/v1/documents/{str(doc.id)}", headers=headers)
            assert res.status_code == 200

        # 3. Delete Document
        with patch("app.modules.documents.service.DocumentService.delete_document", new_callable=AsyncMock) as mock_del:
            mock_del.return_value = {"message": "Deleted"}
            res = await client.delete(f"/api/v1/documents/{str(doc.id)}", headers=headers)
            assert res.status_code == 200

        # 4. Get Versions
        with patch("app.modules.documents.service.DocumentService.get_document_versions", new_callable=AsyncMock) as mock_ver:
            mock_ver.return_value = [doc]
            res = await client.get(f"/api/v1/documents/{str(doc.id)}/versions", headers=headers)
            assert res.status_code == 200

    app.dependency_overrides.clear()
