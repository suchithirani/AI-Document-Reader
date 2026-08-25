from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId

from app.common.constants import DocumentStatus
from app.common.exceptions.auth import BadRequestException
from app.modules.documents.document_process_service import DocumentProcessingService


@pytest.mark.asyncio
async def test_document_processing_service_validation(mock_db):
    service = DocumentProcessingService(mock_db)
    with pytest.raises(BadRequestException):
        await service.process_documents(owner_id="u1", document_ids=[])


@pytest.mark.asyncio
async def test_document_processing_service_full_pipeline(mock_db, test_user):
    service = DocumentProcessingService(mock_db)
    now = datetime.now(UTC)

    # Insert test document
    doc_id = str(ObjectId())
    await mock_db["documents"].insert_one({
        "_id": ObjectId(doc_id),
        "owner_id": str(test_user.id),
        "original_filename": "invoice.pdf",
        "filename": f"{doc_id}_invoice.pdf",
        "storage_provider": "local",
        "storage_path": f"uploads/{doc_id}_invoice.pdf",
        "mime_type": "application/pdf",
        "extension": ".pdf",
        "file_size": 1024,
        "status": DocumentStatus.UPLOADED,
        "is_latest": True,
        "version": 1,
        "version_group_id": "vg1",
        "created_at": now,
        "updated_at": now,
    })

    # Mock storage, OCR, embeddings, and Qdrant
    with patch.object(service.storage_service, "get_file_path", return_value="dummy_path.pdf"), \
         patch.object(service.ocr_service, "extract_text", return_value=["Page 1 sample invoice text"]), \
         patch.object(service.embedding_service, "create_embeddings", new_callable=AsyncMock) as mock_embed, \
         patch.object(service.qdrant_repo, "upsert_chunks") as mock_qdrant, \
         patch("app.ocr.quality.calculate_document_quality", return_value=95.0), \
         patch.object(service.pdf_image_extractor, "extract_images", return_value=[]), \
         patch("app.workers.ai_tasks.extract_document_metadata_task.delay"), \
         patch("app.workers.ai_tasks.generate_proactive_insights_task.delay"):

        mock_embed.return_value = [[0.1] * 768]

        await service.process_documents(
            owner_id=str(test_user.id),
            document_ids=[doc_id],
        )

        doc = await mock_db["documents"].find_one({"_id": ObjectId(doc_id)})
        assert doc["status"] == DocumentStatus.READY
