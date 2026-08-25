from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.ai_tasks import (
    run_extract_document_metadata,
    run_proactive_insights,
    run_update_user_memory,
)


@pytest.mark.asyncio
async def test_ai_tasks_async_proactive_insights_execution(mock_db, test_user):
    with patch("app.workers.ai_tasks.get_worker_database", new_callable=AsyncMock) as mock_get_db, \
         patch("app.modules.search.service.SearchService._run_extraction_pipeline", new_callable=AsyncMock) as mock_extract, \
         patch("app.services.ai.service.AIService.answer_question", new_callable=AsyncMock) as mock_ai:

        mock_get_db.return_value = (MagicMock(), mock_db)
        mock_extract.return_value = ("| Table |", [], [])
        mock_ai.return_value = {"answer": "Proactive insight analysis completed."}

        # 1. Run proactive insights
        await run_proactive_insights(owner_id=str(test_user.id), document_ids=["doc_1"])


@pytest.mark.asyncio
async def test_ai_tasks_async_user_memory_and_metadata(mock_db, test_user):
    with patch("app.workers.ai_tasks.get_worker_database", new_callable=AsyncMock) as mock_get_db, \
         patch("app.services.ai.service.AIService.answer_question", new_callable=AsyncMock) as mock_ai:

        mock_get_db.return_value = (MagicMock(), mock_db)
        mock_ai.return_value = {"answer": "User preferred currency: USD"}

        # 1. Run update user memory
        await run_update_user_memory(owner_id=str(test_user.id), session_id="s1")

        # 2. Run extract document metadata
        await run_extract_document_metadata(owner_id=str(test_user.id), document_id="d1")
