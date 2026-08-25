from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.constants import DocumentStatus
from app.common.exceptions.auth import BadRequestException, ForbiddenException, NotFoundException
from app.common.exceptions.document import DocumentNotFoundException
from app.modules.chat.service import ChatService


@pytest.mark.asyncio
async def test_chat_service_create_session_validation(mock_db):
    service = ChatService(mock_db)

    # 1. Empty document_ids
    with pytest.raises(BadRequestException, match="No documents linked"):
        await service.create_session(owner_id="user1", document_ids=[])

    # 2. Document does not exist
    service.document_repository.get_document_by_id = AsyncMock(return_value=None)
    with pytest.raises(DocumentNotFoundException):
        await service.create_session(owner_id="user1", document_ids=["doc_missing"])

    # 3. Document owner mismatch
    unowned_doc = MagicMock(id="doc_other", owner_id="user2", status=DocumentStatus.READY)
    service.document_repository.get_document_by_id = AsyncMock(return_value=unowned_doc)
    with pytest.raises(ForbiddenException):
        await service.create_session(owner_id="user1", document_ids=["doc_other"])

    # 4. Document not ready
    unprocessed_doc = MagicMock(id="doc_proc", owner_id="user1", status=DocumentStatus.OCR_PROCESSING)
    service.document_repository.get_document_by_id = AsyncMock(return_value=unprocessed_doc)
    with pytest.raises(BadRequestException, match="has not been processed yet"):
        await service.create_session(owner_id="user1", document_ids=["doc_proc"])


@pytest.mark.asyncio
async def test_chat_service_session_access_control(mock_db):
    service = ChatService(mock_db)

    # 1. Non-existent session
    service.repository.get_session = AsyncMock(return_value=None)
    with pytest.raises(NotFoundException):
        await service.rename_session(owner_id="user1", session_id="s_missing", title="New")

    with pytest.raises(NotFoundException):
        await service.delete_session(owner_id="user1", session_id="s_missing")

    with pytest.raises(NotFoundException):
        await service.send_message(owner_id="user1", session_id="s_missing", question="Hello")

    # 2. Owner mismatch
    other_session = MagicMock(id="s_other", owner_id="user2")
    service.repository.get_session = AsyncMock(return_value=other_session)
    with pytest.raises(ForbiddenException):
        await service.rename_session(owner_id="user1", session_id="s_other", title="New")

    with pytest.raises(ForbiddenException):
        await service.delete_session(owner_id="user1", session_id="s_other")

    with pytest.raises(ForbiddenException):
        await service.send_message(owner_id="user1", session_id="s_other", question="Hello")
