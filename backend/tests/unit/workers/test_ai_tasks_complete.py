from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.ai_tasks import (
    run_extract_document_metadata,
    run_proactive_insights,
    run_update_user_memory,
)


@pytest.mark.asyncio
async def test_run_proactive_insights():
    with patch("app.workers.ai_tasks.get_worker_database") as mock_get_db, \
         patch("app.workers.ai_tasks.SearchService") as MockSearchService, \
         patch("app.workers.ai_tasks.ChatService") as MockChatService, \
         patch("app.workers.ai_tasks.AIService") as MockAIService:

        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_get_db.return_value = (mock_client, mock_db)

        mock_search = MagicMock()
        mock_search._run_extraction_pipeline = AsyncMock(
            return_value=("| Doc | Total |\n|---|---|\n| inv1 | $100 |", [], [])
        )
        mock_search._get_document_metadata = AsyncMock(
            return_value=[{"document_name": "Invoice 101.pdf"}]
        )
        MockSearchService.return_value = mock_search

        mock_chat = MagicMock()
        mock_session = MagicMock(id="sess_123")
        mock_chat.create_session = AsyncMock(return_value=mock_session)
        mock_chat.repository.create_message = AsyncMock(return_value=True)
        mock_chat.repository.update = AsyncMock(return_value=True)
        MockChatService.return_value = mock_chat

        mock_ai = MagicMock()
        mock_ai.answer_question = AsyncMock(return_value={"answer": "I have analyzed your invoice."})
        MockAIService.return_value = mock_ai

        await run_proactive_insights(owner_id="user_123", document_ids=["doc_123"])
        assert mock_search._run_extraction_pipeline.called
        assert mock_ai.answer_question.called
        assert mock_chat.create_session.called


@pytest.mark.asyncio
async def test_run_update_user_memory(mock_db):
    with patch("app.workers.ai_tasks.get_worker_database") as mock_get_db, \
         patch("app.workers.ai_tasks.ChatService") as MockChatService, \
         patch("app.workers.ai_tasks.AIService") as MockAIService:

        mock_get_db.return_value = (MagicMock(), mock_db)

        mock_chat = MagicMock()
        mock_msg = MagicMock(role="user", content="Remember my invoice prefix is INV-")
        mock_chat.repository.get_messages = AsyncMock(return_value=[mock_msg])
        MockChatService.return_value = mock_chat

        mock_ai = MagicMock()
        mock_ai.answer_question = AsyncMock(
            side_effect=[
                {"answer": '["User invoice prefix is INV-"]'},
                {"answer": '["User invoice prefix is INV-"]'},
            ]
        )
        MockAIService.return_value = mock_ai

        await run_update_user_memory(owner_id="user_123", session_id="sess_123")
        assert mock_ai.answer_question.called


@pytest.mark.asyncio
async def test_run_extract_document_metadata(mock_db):
    with patch("app.workers.ai_tasks.get_worker_database") as mock_get_db, \
         patch("app.workers.ai_tasks.AIService") as MockAIService:

        mock_get_db.return_value = (MagicMock(), mock_db)

        mock_ai = MagicMock()
        mock_ai.answer_question = AsyncMock(
            return_value={"answer": '{"document_type": "invoice", "description": "Bill for services", "tags": ["tax"], "extracted_metadata": {"total": 500}}'}
        )
        MockAIService.return_value = mock_ai

        # Insert mock chunk in mock_db
        await mock_db["document_chunks"].insert_one({
            "document_id": "doc_123",
            "index": 0,
            "text": "Invoice #101 Total: $500",
        })

        await run_extract_document_metadata(owner_id="user_123", document_id="doc_123")
        assert mock_ai.answer_question.called
