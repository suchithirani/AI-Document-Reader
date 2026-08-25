from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.constants import DocumentStatus
from app.modules.documents.document_process_service import DocumentProcessingService
from app.modules.documents.model import Document


@pytest.mark.asyncio
async def test_document_process_service_batch_success(mock_db, test_user):
    service = DocumentProcessingService(mock_db)

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
        page_count=1,
        status=DocumentStatus.QUEUED,
        progress=0,
        version=1,
        is_latest=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    service.repository.get_document_by_id = AsyncMock(return_value=mock_doc)
    service.repository.update_status = AsyncMock(return_value=True)
    service.repository.update = AsyncMock(return_value=True)
    service.processing_lock_service.acquire = AsyncMock(return_value=True)
    service.processing_lock_service.release = AsyncMock(return_value=True)
    service.processing_lock_service.close = AsyncMock(return_value=True)

    # Mock OCR
    service.ocr_service.extract_text = MagicMock(return_value=["Page 1 extracted OCR text content."])

    # Mock images
    service.pdf_image_extractor.extract_images = MagicMock(return_value=[])

    # Mock embeddings & Qdrant
    service.embedding_service.create_embeddings = AsyncMock(return_value=[[0.1] * 768])
    service.qdrant_repo.upsert = MagicMock(return_value=True)
    service.document_chunk_service.get_chunks_with_embeddings = AsyncMock(return_value=[MagicMock()])

    with patch("app.workers.ai_tasks.generate_proactive_insights_task.delay") as mock_proactive, \
         patch("app.workers.ai_tasks.extract_document_metadata_task.delay") as mock_meta:

        await service.process_documents(
            owner_id=str(test_user.id),
            document_ids=["6a8b765d9a8f6b09441789a0"],
        )
        assert service.repository.update_status.called


@pytest.mark.asyncio
async def test_document_process_service_single_process(mock_db, test_user):
    service = DocumentProcessingService(mock_db)

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
        page_count=1,
        status=DocumentStatus.QUEUED,
        progress=0,
        version=1,
        is_latest=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    service.repository.get_document_by_id = AsyncMock(return_value=mock_doc)
    service.repository.update_status = AsyncMock(return_value=True)
    service.repository.update = AsyncMock(return_value=True)
    service.processing_lock_service.acquire = AsyncMock(return_value=True)
    service.processing_lock_service.release = AsyncMock(return_value=True)
    service.processing_lock_service.close = AsyncMock(return_value=True)
    service.ocr_service.extract_text = MagicMock(return_value=["Single document text."])
    service.pdf_image_extractor.extract_images = MagicMock(return_value=[])
    service.embedding_service.create_embeddings = AsyncMock(return_value=[[0.1] * 768])
    service.qdrant_repo.upsert = MagicMock(return_value=True)
    service.document_chunk_service.get_chunks_with_embeddings = AsyncMock(return_value=[MagicMock()])

    with patch("app.workers.ai_tasks.extract_document_metadata_task.delay"):
        await service.process(
            owner_id=str(test_user.id),
            document_id="6a8b765d9a8f6b09441789a0",
        )
