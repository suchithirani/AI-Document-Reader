from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.search.service import SearchService


@pytest.mark.asyncio
async def test_search_service_streaming(mock_db):
    service = SearchService(mock_db)

    # Mock analyzer
    service.query_analyzer.analyze = MagicMock(
        return_value=MagicMock(
            intent="factual",
            scope="global",
            query_type="factual",
            search_terms=["invoice"],
            is_broad=False,
            is_broad_query=False,
            requires_visual=False,
            target_pages=[],
            page_numbers=[],
        )
    )

    # Mock metadata
    service._get_document_metadata = AsyncMock(
        return_value=[{"document_id": "doc_1", "document_name": "Invoice.pdf", "page_count": 1}]
    )

    # Mock retrieval
    service.retrieval_service.retrieve_candidates = AsyncMock(
        return_value=[
            {
                "document_id": "doc_1",
                "document_name": "Invoice.pdf",
                "page_number": 1,
                "text": "Invoice total: 1000",
                "score": 0.95,
                "chunk_index": 0,
            }
        ]
    )

    service.token_budget_service.allocate_budget = MagicMock(
        return_value=(
            [
                {
                    "document_id": "doc_1",
                    "document_name": "Invoice.pdf",
                    "page_number": 1,
                    "text": "Invoice total: 1000",
                    "score": 0.95,
                    "chunk_index": 0,
                }
            ],
            100,
        )
    )

    async def fake_stream(*args, **kwargs):
        yield "Invoice "
        yield "total is "
        yield "$1000."

    service.ai_service.answer_question_stream = fake_stream

    chunks_received = []
    async for item in service.search_stream(
        question="What is the invoice total?",
        document_ids=["doc_1"],
        owner_id="user_123",
        session_id="s1",
    ):
        chunks_received.append(item)

    assert len(chunks_received) >= 1
