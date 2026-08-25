from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.exceptions.auth import BadRequestException, ForbiddenException, NotFoundException
from app.modules.documents.service import DocumentService


@pytest.mark.asyncio
async def test_document_service_upload_limit(mock_db, test_user):
    service = DocumentService(mock_db)
    mock_files = [MagicMock() for _ in range(11)]
    mock_http_req = MagicMock()

    with pytest.raises(BadRequestException, match="Maximum 10 files"):
        await service.upload_document(mock_http_req, test_user, mock_files)


@pytest.mark.asyncio
async def test_document_service_access_control(mock_db, test_user):
    service = DocumentService(mock_db)
    mock_http_req = MagicMock()

    # 1. Document not found
    service.repository.get_document_by_id = AsyncMock(return_value=None)
    with pytest.raises(NotFoundException):
        await service.get_document(test_user, "non_existent_doc")

    with pytest.raises(NotFoundException):
        await service.delete_document(mock_http_req, test_user, "non_existent_doc")

    with pytest.raises(NotFoundException):
        await service.get_document_versions(test_user, "non_existent_doc")

    # 2. Unauthorized owner access
    other_user_doc = MagicMock(
        id="doc_other",
        owner_id="different_owner_999",
        storage_path="/tmp/test.pdf",
        original_filename="confidential.pdf",
        mime_type="application/pdf",
        file_size=1024,
    )
    service.repository.get_document_by_id = AsyncMock(return_value=other_user_doc)

    with pytest.raises(ForbiddenException):
        await service.get_document(test_user, "doc_other")

    with pytest.raises(ForbiddenException):
        await service.delete_document(mock_http_req, test_user, "doc_other")

    with pytest.raises(ForbiddenException):
        await service.get_document_versions(test_user, "doc_other")


@pytest.mark.asyncio
async def test_document_service_delete_success(mock_db, test_user):
    service = DocumentService(mock_db)
    mock_http_req = MagicMock()

    my_doc = MagicMock(
        id="doc_my",
        owner_id=str(test_user.id),
        storage_path="/tmp/my_file.pdf",
        original_filename="my_file.pdf",
        mime_type="application/pdf",
        file_size=2048,
        is_latest=True,
        version_group_id=None,
    )
    service.repository.get_document_by_id = AsyncMock(return_value=my_doc)
    service.storage_service.delete_file = AsyncMock(return_value=True)
    service.repository.soft_delete = AsyncMock(return_value=True)
    service.audit_log_service.create_log = AsyncMock(return_value=True)
    service.response_cache.delete = AsyncMock(return_value=True)

    res = await service.delete_document(mock_http_req, test_user, "doc_my")
    assert res["message"] == "Document deleted successfully."
    assert service.storage_service.delete_file.called
    assert service.repository.soft_delete.called
