from datetime import UTC, datetime

import pytest
from bson import ObjectId

from app.common.constants import DocumentStatus
from app.common.exceptions.auth import ForbiddenException, NotFoundException
from app.modules.document_collections.service import DocumentCollectionService


@pytest.mark.asyncio
async def test_document_collections_complete_lifecycle(mock_db, test_user):
    service = DocumentCollectionService(mock_db)
    now = datetime.now(UTC)

    # 1. Insert a mock document
    doc_id = str(ObjectId())
    await mock_db["documents"].insert_one({
        "_id": ObjectId(doc_id),
        "owner_id": str(test_user.id),
        "original_filename": "sample.pdf",
        "filename": "sample.pdf",
        "storage_provider": "local",
        "storage_path": "uploads/sample.pdf",
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

    # 2. Create collection (Document Not Found error)
    with pytest.raises(NotFoundException):
        await service.create_collection(
            owner_id=str(test_user.id),
            name="Test Collection",
            description="A description",
            document_ids=[str(ObjectId())],
        )

    # 3. Create collection (Success)
    col = await service.create_collection(
        owner_id=str(test_user.id),
        name="Finance Docs",
        description="Invoices & Reports",
        document_ids=[doc_id],
    )
    col_id = str(col.id)
    assert col.name == "Finance Docs"

    # 4. Get Collections
    cols = await service.get_collections(owner_id=str(test_user.id))
    assert len(cols) >= 1

    # 5. Get Single Collection
    c_single = await service.get_collection(owner_id=str(test_user.id), collection_id=col_id)
    assert c_single.id == col.id

    # 6. Get Collection (Not Found & Forbidden)
    with pytest.raises(NotFoundException):
        await service.get_collection(owner_id=str(test_user.id), collection_id=str(ObjectId()))

    with pytest.raises(ForbiddenException):
        await service.get_collection(owner_id="other_user_999", collection_id=col_id)

    # 7. Update Collection
    updated = await service.update_collection(
        owner_id=str(test_user.id),
        collection_id=col_id,
        name="Finance Docs Updated",
        description=None,
        document_ids=[doc_id],
    )
    assert updated.name == "Finance Docs Updated"

    # 8. Delete Collection
    await service.delete_collection(owner_id=str(test_user.id), collection_id=col_id)
