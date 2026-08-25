from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.search.service import SearchService


@pytest.mark.asyncio
async def test_end_to_end_multi_document_comparison(mock_db, mock_gemini_service, mock_embedding_service, mock_qdrant):
    search_service = SearchService(mock_db)

    # Mock dependencies
    search_service.ai_service = mock_gemini_service
    search_service.embedding_service = mock_embedding_service
    search_service.vector_service.search = MagicMock(return_value=[
        {
            "chunk": MagicMock(
                id="c1",
                document_id="doc1",
                document_name="AI Roadmap.pdf",
                page_number=1,
                chunk_index=0,
                text="AI Learning Roadmap curriculum.",
            ),
            "score": 0.92,
        },
        {
            "chunk": MagicMock(
                id="c2",
                document_id="doc2",
                document_name="Campaign PPT.pdf",
                page_number=1,
                chunk_index=0,
                text="Digital Campaign Project Presentation.",
            ),
            "score": 0.91,
        }
    ])
    search_service.embedding_cache.get = AsyncMock(return_value=None)
    search_service.embedding_cache.set = AsyncMock(return_value=None)

    async def mock_get_doc(doc_id):
        if doc_id == "doc1":
            return MagicMock(
                id="doc1",
                original_filename="AI Roadmap.pdf",
                page_count=3,
                file_size=2048,
                mime_type="application/pdf",
                status="ready"
            )
        return MagicMock(
            id="doc2",
            original_filename="Campaign PPT.pdf",
            page_count=5,
            file_size=4096,
            mime_type="application/pdf",
            status="ready"
        )

    search_service.document_repository.get_document_by_id = AsyncMock(side_effect=mock_get_doc)

    mock_chunks = [
        MagicMock(id="c1", document_id="doc1", page_number=1, chunk_index=0, text="AI Learning Roadmap curriculum."),
        MagicMock(id="c2", document_id="doc2", page_number=1, chunk_index=0, text="Digital Campaign Project Presentation.")
    ]
    search_service.chunk_service.get_chunks_by_document_ids = AsyncMock(return_value=mock_chunks)

    result = await search_service.search(
        owner_id="user_123",
        session_id="session_123",
        document_ids=["doc1", "doc2"],
        question="Compare the topics and scope of these two files.",
    )

    assert "answer" in result
    assert len(result["sources"]["content"]) >= 1
