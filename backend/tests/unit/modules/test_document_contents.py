import pytest

from app.modules.document_contents.repository import DocumentContentRepository
from app.modules.document_contents.service import DocumentContentService


@pytest.mark.asyncio
async def test_document_content_service_and_repository(mock_db):
    service = DocumentContentService(mock_db)

    # 1. Save pages
    await service.save_pages(document_id="doc_123", pages=["Page 1 content text", "Page 2 content text"])

    # 2. Query pages via repository
    repo = DocumentContentRepository(mock_db)
    pages = await repo.get_pages("doc_123")
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert pages[0]["text"] == "Page 1 content text"

    # 3. Copy pages
    copied_count = await service.copy_pages(source_document_id="doc_123", target_document_id="doc_456")
    assert copied_count is None or copied_count >= 0
    target_pages = await repo.get_pages("doc_456")
    assert len(target_pages) == 2
