from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.exceptions.search import SearchException
from app.modules.search.service import SearchService


@pytest.mark.asyncio
async def test_search_service_visual_and_table_edge_cases(mock_db):
    service = SearchService(mock_db)

    # 1. Vision with empty vision results
    service.query_analyzer.analyze = MagicMock(
        return_value=MagicMock(
            intent="visual",
            scope="global",
            query_type="visual",
            search_terms=["chart"],
            is_broad=False,
            is_broad_query=False,
            requires_visual=True,
            target_pages=[1],
            page_numbers=[1],
        )
    )
    service._get_document_metadata = AsyncMock(
        return_value=[{"document_id": "doc_1", "document_name": "Chart.pdf", "page_count": 1}]
    )
    service.vision_service.process_query = AsyncMock(return_value=[]) # Empty vision results fallback
    service.retrieval_service.retrieve_candidates = AsyncMock(return_value=[])
    service.token_budget_service.allocate_budget = MagicMock(return_value=([], 0))
    service.prompt_builder.build = MagicMock(return_value="Prompt")
    service.ai_service.answer_question = AsyncMock(return_value={"answer": "No visual elements found."})

    res = await service.search(
        question="Show me the chart on page 1",
        document_ids=["doc_1"],
        owner_id="user_123",
        session_id="s1",
    )
    assert res is not None


@pytest.mark.asyncio
async def test_search_service_error_handling(mock_db):
    service = SearchService(mock_db)
    service.query_analyzer.analyze = MagicMock(side_effect=RuntimeError("Unexpected analyzer crash"))

    with pytest.raises(SearchException):
        await service.search(
            question="Crash query",
            document_ids=["doc_1"],
            owner_id="user_123",
            session_id="s1",
        )
