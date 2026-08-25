from datetime import UTC, datetime

import pytest
from bson import ObjectId

from app.common.constants import ChatRole, DocumentStatus
from app.modules.chat.service import ChatService


@pytest.mark.asyncio
async def test_chat_service_streaming_message(mock_db, test_user):
    service = ChatService(mock_db)
    now = datetime.now(UTC)

    # Insert document
    doc_id = str(ObjectId())
    await mock_db["documents"].insert_one({
        "_id": ObjectId(doc_id),
        "owner_id": str(test_user.id),
        "original_filename": "guide.pdf",
        "filename": "guide.pdf",
        "storage_provider": "local",
        "storage_path": "uploads/guide.pdf",
        "mime_type": "application/pdf",
        "extension": ".pdf",
        "file_size": 1024,
        "status": DocumentStatus.READY,
        "is_latest": True,
        "version": 1,
        "version_group_id": "vg1",
        "created_at": now,
        "updated_at": now,
    })

    # Create session
    session = await service.create_session(
        owner_id=str(test_user.id),
        document_ids=[doc_id],
    )
    session_id = str(session.id)

    # Mock search service streaming
    async def fake_search_stream(*args, **kwargs):
        yield {"type": "sources", "content": {"metadata": [], "content": []}}
        yield {"type": "chunk", "content": "Hello "}
        yield {"type": "chunk", "content": "World!"}
        yield {"type": "done", "content": "Hello World!"}

    service.search_service.search_stream = fake_search_stream

    events = []
    async for event in service.send_message_stream(
        session_id=session_id,
        owner_id=str(test_user.id),
        question="What is this document?",
    ):
        events.append(event)

    assert len(events) >= 1


@pytest.mark.asyncio
async def test_chat_service_history_and_deletion(mock_db, test_user):
    service = ChatService(mock_db)
    now = datetime.now(UTC)

    doc_id = str(ObjectId())
    await mock_db["documents"].insert_one({
        "_id": ObjectId(doc_id),
        "owner_id": str(test_user.id),
        "original_filename": "guide.pdf",
        "filename": "guide.pdf",
        "storage_provider": "local",
        "storage_path": "uploads/guide.pdf",
        "mime_type": "application/pdf",
        "extension": ".pdf",
        "file_size": 1024,
        "status": DocumentStatus.READY,
        "is_latest": True,
        "version": 1,
        "version_group_id": "vg1",
        "created_at": now,
        "updated_at": now,
    })

    session = await service.create_session(
        owner_id=str(test_user.id),
        document_ids=[doc_id],
    )
    session_id = str(session.id)

    # Add message
    await service.repository.create_message({
        "session_id": session_id,
        "role": ChatRole.USER,
        "content": "Test question",
        "created_at": now,
        "updated_at": now,
    })

    # Get history
    history = await service.get_history(session_id=session_id, owner_id=str(test_user.id))
    assert len(history) >= 1

    # Rename session
    renamed = await service.rename_session(session_id=session_id, owner_id=str(test_user.id), title="Renamed Session")
    assert renamed.title == "Renamed Session"

    # Delete session
    del_res = await service.delete_session(session_id=session_id, owner_id=str(test_user.id))
    assert str(del_res.id) == session_id
