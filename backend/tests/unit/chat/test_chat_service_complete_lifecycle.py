from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.constants import DocumentStatus
from app.modules.chat.service import ChatService
from app.modules.documents.model import Document


@pytest.mark.asyncio
async def test_chat_service_full_workflow(mock_db, test_user):
    service = ChatService(mock_db)

    mock_doc = Document(
        _id="6a8b765d9a8f6b09441789a0",
        owner_id=str(test_user.id),
        original_filename="sample.pdf",
        filename="12345_sample.pdf",
        storage_provider="local",
        storage_path="uploads/sample.pdf",
        mime_type="application/pdf",
        extension=".pdf",
        file_size=1024,
        status=DocumentStatus.READY,
        progress=100,
        version=1,
        is_latest=True,
    )
    service.document_repository.get_document_by_id = AsyncMock(return_value=mock_doc)

    # 1. Create Session
    mock_session = MagicMock(id="sess_123", owner_id=str(test_user.id), title="New Chat", title_generated=False, summary=None)
    service.repository.create_session = AsyncMock(return_value=mock_session)
    service.chat_session_document_repository.add_documents = AsyncMock(return_value=True)

    created = await service.create_session(
        owner_id=str(test_user.id),
        document_ids=["6a8b765d9a8f6b09441789a0"],
    )
    assert created.id == "sess_123"

    # 2. Get Sessions
    service.repository.get_sessions = AsyncMock(return_value=[mock_session])
    sessions = await service.get_sessions(owner_id=str(test_user.id))
    assert len(sessions) == 1

    # 3. Rename & Delete Session
    service.repository.get_session = AsyncMock(return_value=mock_session)
    service.repository.update_session_title = AsyncMock(return_value=True)
    service.repository.delete_session = AsyncMock(return_value=True)

    await service.rename_session(owner_id=str(test_user.id), session_id="sess_123", title="Renamed Title")
    await service.delete_session(owner_id=str(test_user.id), session_id="sess_123")

    # 4. Send Message
    service.chat_session_document_repository.get_document_ids = AsyncMock(return_value=["6a8b765d9a8f6b09441789a0"])
    service.repository.get_messages = AsyncMock(return_value=[MagicMock()])
    service.repository.mark_title_generated = AsyncMock(return_value=True)
    service.repository.create_message = AsyncMock(return_value=MagicMock(id="msg_123"))
    service.search_service.search = AsyncMock(return_value={"answer": "42", "sources": {"metadata": [], "content": []}})

    with patch("app.modules.chat.service.generate_chat_title_task.delay") as mock_title_task, \
         patch("app.modules.chat.service.generate_summary_task.delay") as mock_summary_task, \
         patch("app.workers.ai_tasks.update_user_memory_task.delay") as mock_mem_task:

        res = await service.send_message(
            owner_id=str(test_user.id),
            session_id="sess_123",
            question="What is the answer?",
        )
        assert res["answer"] == "42"
        assert mock_title_task.called
