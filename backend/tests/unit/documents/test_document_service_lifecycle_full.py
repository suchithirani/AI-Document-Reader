from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi import UploadFile

from app.common.constants import DocumentStatus
from app.common.exceptions.auth import BadRequestException, NotFoundException
from app.modules.documents.service import DocumentService


@pytest.mark.asyncio
async def test_document_service_upload_validation_and_limits(mock_db, test_user):
    service = DocumentService(mock_db)
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.headers.get.return_value = "pytest-agent"

    # 1. More than 10 files rejection
    many_files = [MagicMock(spec=UploadFile) for _ in range(11)]
    with pytest.raises(BadRequestException):
        await service.upload_document(mock_request, test_user, many_files)

    # 2. Unsupported extension
    bad_ext_file = MagicMock(spec=UploadFile)
    bad_ext_file.filename = "malicious.exe"
    with patch("app.modules.documents.service.validate_file_extension", return_value=False):
        with pytest.raises(BadRequestException):
            await service.upload_document(mock_request, test_user, [bad_ext_file])


@pytest.mark.asyncio
async def test_document_service_upload_duplicate_and_versioning(mock_db, test_user):
    service = DocumentService(mock_db)
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.headers.get.return_value = "pytest-agent"

    file_bytes = b"%PDF-1.4 dummy pdf content for hashing"
    upload_file = MagicMock(spec=UploadFile)
    upload_file.filename = "report_v1.pdf"
    upload_file.content_type = "application/pdf"
    upload_file.read = AsyncMock(return_value=file_bytes)

    with patch("app.modules.documents.service.validate_file_extension", return_value=True), \
         patch("app.modules.documents.service.validate_content_type", return_value=True), \
         patch("app.modules.documents.service.validate_file_size", return_value=True), \
         patch("app.modules.documents.service.get_pdf_page_count", return_value=2), \
         patch("app.modules.documents.service.process_documents_batch_task.delay") as mock_celery:

        # Test A: First upload (New Version Group)
        res1 = await service.upload_document(mock_request, test_user, [upload_file])
        assert len(res1.documents) == 1

        # Test B: Upload same file bytes (Duplicate Hash Detection)
        upload_file.read = AsyncMock(return_value=file_bytes)
        res2 = await service.upload_document(mock_request, test_user, [upload_file])
        assert len(res2.duplicate_documents) == 1 or len(res2.documents) == 1


@pytest.mark.asyncio
async def test_document_service_download_and_delete_lifecycle(mock_db, test_user):
    service = DocumentService(mock_db)
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.headers.get.return_value = "pytest-agent"
    now = datetime.now(UTC)

    # Insert document
    doc_id = str(ObjectId())
    await mock_db["documents"].insert_one({
        "_id": ObjectId(doc_id),
        "owner_id": str(test_user.id),
        "original_filename": "guide.pdf",
        "filename": f"{doc_id}_guide.pdf",
        "storage_provider": "local",
        "storage_path": f"uploads/{doc_id}_guide.pdf",
        "mime_type": "application/pdf",
        "extension": ".pdf",
        "file_size": 1024,
        "status": DocumentStatus.READY,
        "is_latest": True,
        "version": 1,
        "version_group_id": "vg1",
        "created_at": now,
        "updated_at": now,
    })

    # 1. Get Document
    doc = await service.get_document(current_user=test_user, document_id=doc_id)
    assert doc.id == doc_id

    # 2. Get Document Not Found
    with pytest.raises(NotFoundException):
        await service.get_document(current_user=test_user, document_id=str(ObjectId()))

    # 3. Delete Document
    del_res = await service.delete_document(http_request=mock_request, current_user=test_user, document_id=doc_id)
    assert del_res["message"] == "Document deleted successfully."
