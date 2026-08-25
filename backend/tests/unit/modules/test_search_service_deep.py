from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.search.service import SearchService


@pytest.mark.asyncio
async def test_search_service_regular_query(mock_db):
    service = SearchService(mock_db)

    # Mock embedding cache
    service.embedding_cache.get = AsyncMock(return_value=None)
    service.embedding_cache.set = AsyncMock(return_value=True)

    # Mock embedding service
    service.embedding_service.create_embedding = AsyncMock(return_value=[0.1] * 768)

    # Mock document metadata & repo
    service._get_document_metadata = AsyncMock(
        return_value=[
            {
                "document_id": "doc_1",
                "document_name": "Invoice1.pdf",
                "page_count": 1,
            }
        ]
    )

    # Mock analyzer (synchronous method)
    service.query_analyzer.analyze = MagicMock(
        return_value=MagicMock(
            intent="factual",
            scope="global",
            query_type="factual",
            search_terms=["invoice", "total"],
            is_broad=False,
            is_broad_query=False,
            requires_visual=False,
            target_pages=[],
            page_numbers=[],
        )
    )

    # Mock retrieval
    service.retrieval_service.retrieve_candidates = AsyncMock(
        return_value=[
            {
                "document_id": "doc_1",
                "document_name": "Invoice1.pdf",
                "page_number": 1,
                "text": "Invoice #101 Total: $500",
                "score": 0.95,
                "chunk_index": 0,
            }
        ]
    )

    # Mock token budget & prompt builder
    service.token_budget_service.allocate_budget = MagicMock(
        return_value=(
            [
                {
                    "document_id": "doc_1",
                    "document_name": "Invoice1.pdf",
                    "page_number": 1,
                    "text": "Invoice #101 Total: $500",
                    "score": 0.95,
                    "chunk_index": 0,
                }
            ],
            200,
        )
    )
    service.prompt_builder.build = MagicMock(return_value="[Context: Invoice #101 Total: $500] Answer: $500")

    # Mock AI response
    service.ai_service.answer_question = AsyncMock(
        return_value={
            "answer": "The invoice total is $500 [Invoice1.pdf Page 1].",
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "latency_ms": 100.0,
        }
    )

    result = await service.search(
        question="What is the invoice total?",
        document_ids=["doc_1"],
        owner_id="user_123",
        session_id="s1",
    )
    assert "answer" in result


@pytest.mark.asyncio
async def test_search_service_extraction_pipeline(mock_db):
    service = SearchService(mock_db)

    # Mock chunks
    mock_chunk = MagicMock(
        document_id="doc_1",
        page_number=1,
        text="Invoice #101 Date: 12/08/2026 Supplier: ABC Corp Total: $500",
    )
    service.chunk_service.repository.get_document_chunks = AsyncMock(return_value=[mock_chunk])

    # Mock GeminiAIService response with JSON extraction
    with patch("app.services.ai.providers.gemini.GeminiAIService.answer_question", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = {
            "answer": '[{"document_id": "doc_1", "invoice_number": "101", "date": "12/08/2026", "supplier": "ABC Corp", "grand_total": "500", "buyer": "XYZ", "place_of_supply": "GJ", "gstin": "24AAAAA0000A1Z5", "subtotal": "500", "total_gst": "0", "main_products": "Goods", "quantity": "1", "bank_details": "N/A"}]',
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "latency_ms": 120.0,
        }

        table, content_srcs, meta_srcs = await service._run_extraction_pipeline(
            document_ids=["doc_1"],
            question="Compare invoices",
            owner_id="user_123",
        )
        assert table is not None
        assert "ABC Corp" in table or "101" in table
