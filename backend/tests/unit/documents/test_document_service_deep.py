from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.constants import DocumentStatus
from app.modules.documents.model import Document
from app.modules.documents.service import DocumentService


@pytest.mark.asyncio
async def test_document_service_get_and_cache(mock_db, test_user):
    service = DocumentService(mock_db)

    mock_doc = Document(
        _id="6a8b765d9a8f6b09441789a0",
        owner_id=str(test_user.id),
        original_filename="sample.pdf",
        filename="12345_sample.pdf",
        storage_provider="local",
        storage_path="uploads/sample.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        file_size=1024,
        page_count=2,
        status=DocumentStatus.READY,
        progress=100,
        version=1,
        is_latest=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    service.repository.get_documents_by_owner = AsyncMock(return_value=[mock_doc])

    # 1. Get documents (cache miss -> loads from DB -> caches in redis)
    service.response_cache.get = AsyncMock(return_value=None)
    service.response_cache.set = AsyncMock(return_value=True)

    docs = await service.get_documents(current_user=test_user, skip=0, limit=20)
    assert len(docs) == 1
    assert docs[0].original_filename == "sample.pdf"
    assert service.response_cache.set.called

    # 2. Get documents (cache hit)
    service.response_cache.get = AsyncMock(return_value=[docs[0].model_dump(mode="json", by_alias=True)])
    cached_docs = await service.get_documents(current_user=test_user, skip=0, limit=20)
    assert len(cached_docs) == 1


@pytest.mark.asyncio
async def test_document_service_versions_and_count(mock_db, test_user):
    service = DocumentService(mock_db)

    mock_doc = Document(
        _id="6a8b765d9a8f6b09441789a0",
        owner_id=str(test_user.id),
        original_filename="contract.pdf",
        filename="12345_contract.pdf",
        storage_provider="local",
        storage_path="uploads/contract.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        file_size=2048,
        progress=100,
        version=2,
        version_group_id="vg-123",
        status=DocumentStatus.READY,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    service.repository.get_document_by_id = AsyncMock(return_value=mock_doc)
    service.repository.get_versions_by_group = AsyncMock(return_value=[mock_doc])
    service.repository.count_documents = AsyncMock(return_value=5)

    # 1. Get versions
    versions = await service.get_document_versions(current_user=test_user, document_id="6a8b765d9a8f6b09441789a0")
    assert len(versions) == 1

    # 2. Count documents
    count = await service.count_documents(current_user=test_user)
    assert count == 5


@pytest.mark.asyncio
async def test_document_service_process_documents(mock_db, test_user, tmp_path):
    service = DocumentService(mock_db)

    mock_doc = Document(
        _id="6a8b765d9a8f6b09441789a0",
        owner_id=str(test_user.id),
        status=DocumentStatus.UPLOADED,
        storage_provider="local",
        storage_path=str(tmp_path / "test.pdf"),
        original_filename="test.pdf",
        filename="12345_test.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        file_size=1024,
        progress=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    service.repository.get_document_by_id = AsyncMock(return_value=mock_doc)
    service.repository.update_status = AsyncMock(return_value=True)

    mock_req = MagicMock()
    mock_req.client.host = "127.0.0.1"
    mock_req.headers.get.return_value = "Mozilla/5.0"

    with patch("app.modules.documents.service.process_documents_batch_task.delay") as mock_delay:
        res = await service.process_documents(
            http_request=mock_req,
            current_user=test_user,
            document_ids=["6a8b765d9a8f6b09441789a0"],
        )
        assert res["count"] == 1
        assert "6a8b765d9a8f6b09441789a0" in res["queued_documents"]
        assert mock_delay.called
