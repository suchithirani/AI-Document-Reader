import pytest
from bson import ObjectId

from app.repositories.base_repository import BaseRepository


@pytest.mark.asyncio
async def test_base_repository_crud(mock_db):
    collection = mock_db["test_collection"]
    repo = BaseRepository(collection)

    # 1. Create
    created = await repo.create({"title": "Test Title", "category": "AI"})
    assert created is not None
    doc_id = str(created["_id"])
    assert ObjectId.is_valid(doc_id)
    assert created["title"] == "Test Title"

    # 2. Get by ID
    fetched = await repo.get_by_id(doc_id)
    assert fetched is not None
    assert fetched["title"] == "Test Title"

    # 3. Get one by filter
    matched = await repo.get_one({"category": "AI"})
    assert matched is not None
    assert matched["title"] == "Test Title"

    # 4. Count
    count = await repo.count({"category": "AI"})
    assert count == 1
