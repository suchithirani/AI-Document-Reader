import pytest

from app.modules.document_chunks.repository import DocumentChunkRepository
from app.modules.document_chunks.service import DocumentChunkService


@pytest.mark.asyncio
async def test_document_chunk_service_and_repository(mock_db):
    service = DocumentChunkService(mock_db)

    chunks_text = [
        "First sentence with email test@example.com and numbers 12345.",
        "Second sentence containing a table row | Col1 | Col2 |",
    ]

    # 1. Save chunks
    await service.save_chunks(document_id="doc_123", page_number=1, chunks=chunks_text)

    # 2. Query chunks via repository
    repo = DocumentChunkRepository(mock_db)
    db_chunks = await repo.get_document_chunks("doc_123")
    assert len(db_chunks) == 2
    assert db_chunks[0].has_email is True
    assert db_chunks[0].has_numbers is True
    assert db_chunks[1].has_table is True
