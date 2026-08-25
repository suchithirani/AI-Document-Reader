from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.search.service import SearchService


@pytest.mark.asyncio
async def test_search_service_visual_query_pipeline(mock_db):
    service = SearchService(mock_db)

    # Mock analyzer detecting visual query
    service.query_analyzer.analyze = MagicMock(
        return_value=MagicMock(
            intent="visual",
            scope="global",
            query_type="visual",
            search_terms=["chart", "graph"],
            is_broad=False,
            is_broad_query=False,
            requires_visual=True,
            target_pages=[1],
            page_numbers=[1],
        )
    )

    # Mock metadata
    service._get_document_metadata = AsyncMock(
        return_value=[
            {
                "document_id": "doc_1",
                "document_name": "ChartReport.pdf",
                "page_count": 1,
            }
        ]
    )

    # Mock vision pipeline
    service.vision_service.process_query = AsyncMock(
        return_value=[
            {
                "source_id": "vis_1",
                "document_id": "doc_1",
                "page_number": 1,
                "result": "The revenue graph shows steady growth in Q3.",
            }
        ]
    )

    # Mock retrieval candidates
    service.retrieval_service.retrieve_candidates = AsyncMock(
        return_value=[
            {
                "document_id": "doc_1",
                "document_name": "ChartReport.pdf",
                "page_number": 1,
                "text": "Quarterly Revenue Summary",
                "score": 0.90,
                "chunk_index": 0,
            }
        ]
    )

    service.token_budget_service.allocate_budget = MagicMock(
        return_value=(
            [
                {
                    "document_id": "doc_1",
                    "document_name": "ChartReport.pdf",
                    "page_number": 1,
                    "text": "Quarterly Revenue Summary",
                    "score": 0.90,
                    "chunk_index": 0,
                }
            ],
            200,
        )
    )
    service.prompt_builder.build = MagicMock(return_value="[Context: Visual Graph] Answer: Steady growth")
    service.ai_service.answer_question = AsyncMock(
        return_value={
            "answer": "Revenue increased steadily [ChartReport.pdf Page 1].",
            "prompt_tokens": 80,
            "completion_tokens": 30,
            "latency_ms": 110.0,
        }
    )

    result = await service.search(
        question="Show me the revenue chart on page 1",
        document_ids=["doc_1"],
        owner_id="user_123",
        session_id="s1",
    )
    assert "answer" in result


@pytest.mark.asyncio
async def test_search_service_broad_query_pipeline(mock_db):
    service = SearchService(mock_db)

    # Mock broad query (summarize entire document)
    service.query_analyzer.analyze = MagicMock(
        return_value=MagicMock(
            intent="summary",
            scope="global",
            query_type="summary",
            search_terms=["summary", "overview"],
            is_broad=True,
            is_broad_query=True,
            requires_visual=False,
            target_pages=[],
            page_numbers=[],
        )
    )

    service._get_document_metadata = AsyncMock(
        return_value=[
            {
                "document_id": "doc_1",
                "document_name": "FullManual.pdf",
                "page_count": 5,
            }
        ]
    )

    service.retrieval_service.retrieve_candidates = AsyncMock(
        return_value=[
            {
                "document_id": "doc_1",
                "document_name": "FullManual.pdf",
                "page_number": 1,
                "text": "Chapter 1 Introduction and Overview.",
                "score": 0.85,
                "chunk_index": 0,
            }
        ]
    )

    service.token_budget_service.allocate_budget = MagicMock(
        return_value=(
            [
                {
                    "document_id": "doc_1",
                    "document_name": "FullManual.pdf",
                    "page_number": 1,
                    "text": "Chapter 1 Introduction and Overview.",
                    "score": 0.85,
                    "chunk_index": 0,
                }
            ],
            200,
        )
    )
    service.prompt_builder.build = MagicMock(return_value="[Context: Summary] Answer: Complete overview")
    service.ai_service.answer_question = AsyncMock(
        return_value={
            "answer": "This document covers AI architecture and deployment [FullManual.pdf Page 1].",
            "prompt_tokens": 120,
            "completion_tokens": 40,
            "latency_ms": 140.0,
        }
    )

    result = await service.search(
        question="Give me a comprehensive overview of the manual",
        document_ids=["doc_1"],
        owner_id="user_123",
        session_id="s1",
    )
    assert "answer" in result
