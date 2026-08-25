from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.common.constants import CollectionName
from app.workers.ai_tasks import (
    run_extract_document_metadata,
    run_proactive_insights,
    run_update_user_memory,
)


@pytest.mark.asyncio
async def test_run_proactive_insights_workflow(mock_db):
    with patch("app.workers.ai_tasks.get_worker_database", new_callable=AsyncMock) as mock_get_db, \
         patch("app.workers.ai_tasks.SearchService") as mock_search_cls, \
         patch("app.workers.ai_tasks.ChatService") as mock_chat_cls, \
         patch("app.workers.ai_tasks.AIService") as mock_ai_cls:

        mock_get_db.return_value = (MagicMock(), mock_db)

        mock_search = MagicMock()
        mock_search._run_extraction_pipeline = AsyncMock(
            return_value=("| Doc | Total |\n| Invoice1 | 500 |", [], [])
        )
        mock_search._get_document_metadata = AsyncMock(
            return_value=[{"document_name": "Invoice1.pdf"}]
        )
        mock_search_cls.return_value = mock_search

        mock_ai = MagicMock()
        mock_ai.answer_question = AsyncMock(
            return_value={"answer": "Proactive insight: Total invoice is $500."}
        )
        mock_ai_cls.return_value = mock_ai

        mock_chat = MagicMock()
        mock_chat.create_session = AsyncMock(return_value=MagicMock(id="sess_123"))
        mock_chat.repository.create_message = AsyncMock(return_value=True)
        mock_chat.repository.update = AsyncMock(return_value=True)
        mock_chat_cls.return_value = mock_chat

        await run_proactive_insights(
            owner_id="user_123",
            document_ids=["doc_1"],
        )
        assert mock_chat.create_session.called
        assert mock_chat.repository.create_message.called


@pytest.mark.asyncio
async def test_run_update_user_memory_workflow(mock_db):
    with patch("app.workers.ai_tasks.get_worker_database", new_callable=AsyncMock) as mock_get_db, \
         patch("app.workers.ai_tasks.ChatService") as mock_chat_cls, \
         patch("app.workers.ai_tasks.AIService") as mock_ai_cls:

        mock_get_db.return_value = (MagicMock(), mock_db)

        mock_chat = MagicMock()
        mock_msg = MagicMock(role="user", content="Please format amounts in USD.")
        mock_chat.repository.get_messages = AsyncMock(return_value=[mock_msg])
        mock_chat_cls.return_value = mock_chat

        mock_ai = MagicMock()
        mock_ai.answer_question = AsyncMock(
            side_effect=[
                {"answer": '["User prefers USD formatting."]'},
                {"answer": '["User prefers USD formatting."]'},
            ]
        )
        mock_ai_cls.return_value = mock_ai

        await run_update_user_memory(
            owner_id="user_123",
            session_id="sess_123",
        )

        memories_doc = await mock_db[CollectionName.USER_MEMORIES.value].find_one({"owner_id": "user_123"})
        assert memories_doc is not None
        assert "User prefers USD formatting." in memories_doc["memories"]


@pytest.mark.asyncio
async def test_run_extract_document_metadata_workflow(mock_db):
    doc_id = str(ObjectId())

    # Seed chunks
    await mock_db[CollectionName.DOCUMENT_CHUNKS.value].insert_one({
        "document_id": doc_id,
        "content": "TAX INVOICE SMK/436 Supplier: Sheth Matarmal Total: 10080",
        "index": 0,
    })

    # Seed document
    await mock_db[CollectionName.DOCUMENTS.value].insert_one({
        "_id": ObjectId(doc_id),
        "owner_id": "user_123",
        "filename": "sample.pdf",
    })

    with patch("app.workers.ai_tasks.get_worker_database", new_callable=AsyncMock) as mock_get_db, \
         patch("app.workers.ai_tasks.AIService") as mock_ai_cls:

        mock_get_db.return_value = (MagicMock(), mock_db)

        mock_ai = MagicMock()
        mock_ai.answer_question = AsyncMock(
            return_value={
                "answer": '{"document_type": "invoice", "description": "Tax invoice from Sheth Matarmal", "tags": ["tax", "invoice"], "extracted_metadata": {"total": "10080"}}'
            }
        )
        mock_ai_cls.return_value = mock_ai

        await run_extract_document_metadata(
            owner_id="user_123",
            document_id=doc_id,
        )

        updated_doc = await mock_db[CollectionName.DOCUMENTS.value].find_one({"_id": ObjectId(doc_id)})
        assert updated_doc["document_type"] == "invoice"
        assert "tax" in updated_doc["tags"]
