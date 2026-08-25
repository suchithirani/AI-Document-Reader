from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.exceptions.auth import ForbiddenException, NotFoundException
from app.modules.document_collections.service import DocumentCollectionService


@pytest.mark.asyncio
async def test_document_collection_service(mock_db):
    service = DocumentCollectionService(mock_db)

    # 1. Validation: document not found
    service.document_repository.get_document_by_id = AsyncMock(return_value=None)
    with pytest.raises(NotFoundException, match="Document doc_1 not found"):
        await service.create_collection(
            owner_id="user_123",
            name="Invoices 2026",
            description="All 2026 invoices",
            document_ids=["doc_1"],
        )

    # 2. Validation: document not owned
    unowned_doc = MagicMock(owner_id="user_999")
    service.document_repository.get_document_by_id = AsyncMock(return_value=unowned_doc)
    with pytest.raises(ForbiddenException):
        await service.create_collection(
            owner_id="user_123",
            name="Invoices 2026",
            description="All 2026 invoices",
            document_ids=["doc_1"],
        )

    # 3. Successful create & retrieval
    owned_doc = MagicMock(owner_id="user_123")
    service.document_repository.get_document_by_id = AsyncMock(return_value=owned_doc)

    col = await service.create_collection(
        owner_id="user_123",
        name="Tax Documents",
        description="Tax return forms",
        document_ids=["doc_1"],
    )
    assert col.name == "Tax Documents"

    # Get single collection
    fetched = await service.get_collection(owner_id="user_123", collection_id=str(col.id))
    assert fetched.id == col.id

    # Get single collection unauthorized
    with pytest.raises(ForbiddenException):
        await service.get_collection(owner_id="user_other", collection_id=str(col.id))

    # Delete collection
    await service.delete_collection(owner_id="user_123", collection_id=str(col.id))
