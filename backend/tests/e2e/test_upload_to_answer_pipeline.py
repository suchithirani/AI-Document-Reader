from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.search.service import SearchService


@pytest.mark.asyncio
async def test_end_to_end_search_flow(mock_db, mock_gemini_service, mock_embedding_service, mock_qdrant):
    search_service = SearchService(mock_db)

    # Mock AI & Embedding services
    search_service.ai_service = mock_gemini_service
    search_service.embedding_service = mock_embedding_service
    search_service.vector_service.qdrant = mock_qdrant
    search_service.embedding_cache.get = AsyncMock(return_value=None)
    search_service.embedding_cache.set = AsyncMock(return_value=None)

    # Mock Document Retrieval
    mock_doc = MagicMock(
        id="doc1",
        original_filename="sample_roadmap.pdf",
        page_count=3,
        file_size=2048,
        mime_type="application/pdf",
        status="ready"
    )
    search_service.document_repository.get_document_by_id = AsyncMock(return_value=mock_doc)

    # Mock Chunks in DB
    mock_chunk = MagicMock(
        id="chunk1",
        document_id="doc1",
        page_number=1,
        chunk_index=0,
        text="Phase 1: AI Fundamentals and Machine Learning Algorithms."
    )
    search_service.chunk_service.get_chunks_by_document_ids = AsyncMock(return_value=[mock_chunk])

    result = await search_service.search(
        owner_id="user_123",
        session_id="session_123",
        document_ids=["doc1"],
        question="What is in Phase 1?",
    )

    assert "answer" in result
    assert len(result["answer"]) > 0
    assert "sources" in result
