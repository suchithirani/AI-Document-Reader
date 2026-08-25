from datetime import UTC, datetime

import pytest

from app.common.constants import ChatRole, DocumentStatus
from app.modules.auth.repository import UserRepository
from app.modules.chat.repository import ChatRepository
from app.modules.documents.repository import DocumentRepository


@pytest.mark.asyncio
async def test_user_repository_deep(mock_db):
    repo = UserRepository(mock_db)
    now = datetime.now(UTC)
    user_data = {
        "name": "Repo User",
        "email": "repouser@example.com",
        "password_hash": "hash123",
        "phone_number": "+1234567890",
        "is_active": True,
        "is_verified": False,
        "created_at": now,
        "updated_at": now,
    }
    user = await repo.create_user(user_data)
    assert user.email == "repouser@example.com"

    # Get by email
    found = await repo.get_by_email("repouser@example.com")
    assert found is not None

    # Get by phone
    found_phone = await repo.get_by_phone("+1234567890")
    assert found_phone is not None

    # Update password & verify email
    await repo.update_password(str(user.id), "newhash999")
    await repo.verify_email(str(user.id))
    await repo.update_last_login(str(user.id))

    updated = await repo.get_by_id(str(user.id))
    assert updated.is_verified is True
    assert updated.password_hash == "newhash999"


@pytest.mark.asyncio
async def test_chat_repository_deep(mock_db):
    repo = ChatRepository(mock_db)
    now = datetime.now(UTC)
    session = await repo.create_session({
        "owner_id": "user_123",
        "title": "Initial Chat",
        "title_generated": False,
        "created_at": now,
        "updated_at": now,
    })
    session_id = str(session.id)

    # Add message
    msg = await repo.create_message({
        "session_id": session_id,
        "role": ChatRole.USER,
        "content": "Hello AI!",
        "sources": [],
        "created_at": now,
        "updated_at": now,
    })
    assert msg.content == "Hello AI!"

    # Get messages
    msgs = await repo.get_messages(session_id)
    assert len(msgs) == 1

    # Update title and summary
    await repo.update_session_title(session_id, "Updated Chat")
    await repo.mark_title_generated(session_id)
    await repo.update_summary(session_id, "Summary of chat")

    s = await repo.get_session(session_id)
    assert s.title == "Updated Chat"
    assert s.title_generated is True
    assert s.summary == "Summary of chat"


@pytest.mark.asyncio
async def test_document_repository_versions(mock_db):
    repo = DocumentRepository(mock_db)
    now = datetime.now(UTC)

    # Create version 1
    doc1 = await repo.create_document({
        "owner_id": "user_123",
        "original_filename": "guide.pdf",
        "filename": "123_guide.pdf",
        "storage_provider": "local",
        "storage_path": "uploads/123_guide.pdf",
        "mime_type": "application/pdf",
        "extension": ".pdf",
        "file_size": 1024,
        "version": 1,
        "version_group_id": "vg_1",
        "is_latest": True,
        "status": DocumentStatus.READY,
        "created_at": now,
        "updated_at": now,
    })

    # Demote v1 and create v2
    await repo.demote_previous_versions("vg_1")
    doc2 = await repo.create_document({
        "owner_id": "user_123",
        "original_filename": "guide.pdf",
        "filename": "124_guide.pdf",
        "storage_provider": "local",
        "storage_path": "uploads/124_guide.pdf",
        "mime_type": "application/pdf",
        "extension": ".pdf",
        "file_size": 1024,
        "version": 2,
        "version_group_id": "vg_1",
        "is_latest": True,
        "status": DocumentStatus.READY,
        "created_at": now,
        "updated_at": now,
    })

    versions = await repo.get_versions_by_group("vg_1")
    assert len(versions) >= 1

    latest = await repo.get_latest_version_by_name(owner_id="user_123", original_filename="guide.pdf")
    assert latest is not None
    assert latest.version == 2
