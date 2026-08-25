import io
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.dependencies.service import get_document_service
from app.main import app


def test_get_documents_endpoint(test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user

    mock_service = AsyncMock()
    mock_service.get_documents.return_value = [
        {
            "id": "doc1",
            "original_filename": "AI Roadmap.pdf",
            "status": "ready",
            "page_count": 3,
            "file_size": 1024,
        }
    ]
    mock_service.count_documents.return_value = 1
    app.dependency_overrides[get_document_service] = lambda: mock_service

    with TestClient(app) as client:
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["original_filename"] == "AI Roadmap.pdf"

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_document_service, None)


def test_upload_document_endpoint_mocked(test_user):
    app.dependency_overrides[get_current_user] = lambda: test_user

    mock_service = AsyncMock()
    mock_service.upload_document.return_value = {
        "uploaded_files": [
            {"id": "new-doc-id", "filename": "test.pdf", "status": "pending"}
        ]
    }
    app.dependency_overrides[get_document_service] = lambda: mock_service

    with TestClient(app) as client:
        file_payload = ("test.pdf", io.BytesIO(b"%PDF-1.4 sample content"), "application/pdf")
        response = client.post("/api/v1/documents/upload", files={"files": file_payload})
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Document uploaded successfully."

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_document_service, None)
