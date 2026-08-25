import asyncio
import os
import sys
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest  # type: ignore

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx
from fastapi.testclient import TestClient
from httpx import ASGITransport

from app.common.constants import UserRole
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.auth.model import User

# ============================================================================
# Event Loop & Asyncio Setup
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Test User & Authentication Fixtures
# ============================================================================

@pytest.fixture
def mock_user_id() -> str:
    return "6a8b2611d8bb8da18f059a3d"


@pytest.fixture
def mock_admin_id() -> str:
    return "6a8b2611d8bb8da18f059a3e"


@pytest.fixture
def test_user(mock_user_id: str) -> User:
    return User(
        _id=mock_user_id,
        name="Test User",
        email="testuser@example.com",
        password_hash=hash_password("Password123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
        phone_verified=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def admin_user(mock_admin_id: str) -> User:
    return User(
        _id=mock_admin_id,
        name="Admin User",
        email="admin@example.com",
        password_hash=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        phone_verified=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def user_token(test_user: User) -> str:
    return create_access_token(subject=str(test_user.id))


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(subject=str(admin_user.id))


@pytest.fixture
def auth_headers(user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_auth_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================================
# HTTP Test Clients
# ============================================================================

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Mock Database & Repository Fixtures
# ============================================================================

class AsyncMockCollection:
    """Mock MongoDB collection supporting standard async pymongo operations."""
    def __init__(self, name="mock_collection"):
        self.name = name
        self.documents = []

    async def find_one(self, filter=None, *args, **kwargs):
        if not filter:
            return self.documents[0] if self.documents else None
        for doc in self.documents:
            if self._matches(doc, filter):
                return doc
        return None

    def find(self, filter=None, *args, **kwargs):
        class AsyncCursor:
            def __init__(self, docs):
                self.docs = list(docs)
                self._index = 0

            def sort(self, *args, **kwargs):
                return self

            def skip(self, n):
                self.docs = self.docs[n:]
                return self

            def limit(self, n):
                self.docs = self.docs[:n]
                return self

            async def to_list(self, length=None):
                if length is None:
                    return self.docs
                return self.docs[:length]

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self._index < len(self.docs):
                    res = self.docs[self._index]
                    self._index += 1
                    return res
                raise StopAsyncIteration

        matched = []
        if not filter:
            matched = list(self.documents)
        else:
            for doc in self.documents:
                if self._matches(doc, filter):
                    matched.append(doc)
        return AsyncCursor(matched)

    async def insert_one(self, doc, *args, **kwargs):
        new_doc = dict(doc)
        if "_id" not in new_doc:
            import bson
            new_doc["_id"] = bson.ObjectId()
        self.documents.append(new_doc)

        class InsertResult:
            inserted_id = new_doc["_id"]
        return InsertResult()

    async def update_one(self, filter, update, *args, **kwargs):
        doc = await self.find_one(filter)
        upsert = kwargs.get("upsert", False)
        if not doc and upsert:
            new_doc = dict(filter)
            if "$set" in update:
                new_doc.update(update["$set"])
            await self.insert_one(new_doc)
            doc = new_doc
        elif doc and "$set" in update:
            doc.update(update["$set"])
        class UpdateResult:
            matched_count = 1 if doc else 0
            modified_count = 1 if doc else 0
        return UpdateResult()

    async def update_many(self, filter, update, *args, **kwargs):
        matched = [d for d in self.documents if self._matches(d, filter)]
        for doc in matched:
            if "$set" in update:
                doc.update(update["$set"])
        class UpdateManyResult:
            matched_count = len(matched)
            modified_count = len(matched)
        return UpdateManyResult()

    async def find_one_and_update(self, filter, update, *args, **kwargs):
        doc = await self.find_one(filter)
        if doc and "$set" in update:
            doc.update(update["$set"])
        return doc

    async def insert_many(self, docs, *args, **kwargs):
        _ids = []
        for d in docs:
            res = await self.insert_one(d)
            _ids.append(res.inserted_id)
        class InsertManyResult:
            inserted_ids = _ids
        return InsertManyResult()

    async def delete_many(self, filter, *args, **kwargs):
        docs = [d for d in self.documents if self._matches(d, filter)]
        for d in docs:
            self.documents.remove(d)
        class DeleteManyResult:
            deleted_count = len(docs)
        return DeleteManyResult()

    def _matches(self, doc, filter):
        if not filter:
            return True
        for k, v in filter.items():
            if k == "_id" and str(doc.get("_id")) == str(v):
                continue
            if k == "$in" or isinstance(v, dict) and "$in" in v:
                allowed = v["$in"] if isinstance(v, dict) else v
                if doc.get(k) not in allowed:
                    return False
            elif isinstance(v, dict) and "$ne" in v:
                if doc.get(k) == v["$ne"]:
                    return False
            elif doc.get(k) != v:
                return False
        return True

    async def delete_one(self, filter, *args, **kwargs):
        doc = await self.find_one(filter)
        if doc in self.documents:
            self.documents.remove(doc)
        class DeleteResult:
            deleted_count = 1 if doc else 0
        return DeleteResult()

    async def aggregate(self, pipeline, *args, **kwargs):
        class AsyncAggregateCursor:
            def __init__(self, docs):
                self.docs = list(docs)
            async def to_list(self, length=None):
                return self.docs[:length] if length else self.docs

        is_model_split = False
        for stage in pipeline:
            if "$group" in stage and isinstance(stage["$group"].get("_id"), dict):
                is_model_split = True
                break

        if is_model_split:
            return AsyncAggregateCursor([
                {
                    "_id": {"model": "gemini-2.5-flash", "provider": "gemini"},
                    "total_tokens": 150,
                    "requests_count": 10,
                }
            ])

        return AsyncAggregateCursor([
            {
                "_id": "2026-01-01",
                "model": "gemini-2.5-flash",
                "provider": "gemini",
                "total_ai_requests": 10,
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "estimated_cost": 0.005,
                "average_latency": 120.0,
                "average_latency_ms": 120.0,
                "requests_count": 10,
            }
        ])

    async def count_documents(self, filter=None, *args, **kwargs):
        if not filter:
            return len(self.documents)
        count = 0
        for doc in self.documents:
            match = True
            for k, v in filter.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                count += 1
        return count


@pytest.fixture
def mock_db() -> MagicMock:
    db = MagicMock()
    collections = {}

    def get_collection(name: str):
        if name not in collections:
            collections[name] = AsyncMockCollection(name)
        return collections[name]

    db.__getitem__.side_effect = get_collection
    return db


# ============================================================================
# Mock External AI Services (Gemini & Groq)
# ============================================================================

@pytest.fixture
def mock_gemini_service() -> MagicMock:
    mock = MagicMock()
    mock.answer_question = AsyncMock(return_value={
        "answer": "This is a verified test response from the mocked AI model. [1]",
        "prompt_tokens": 50,
        "completion_tokens": 20,
        "total_tokens": 70,
        "latency_ms": 120.5,
    })

    async def mock_stream(prompt: str):
        for chunk in ["This is ", "a streamed ", "test response. [1]"]:
            yield chunk

    mock.answer_question_stream = mock_stream
    return mock


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    mock = MagicMock()
    mock.create_embedding = AsyncMock(return_value=[0.05] * 768)
    mock.generate_embedding = AsyncMock(return_value=[0.05] * 768)
    mock.generate_embeddings = AsyncMock(return_value=[[0.05] * 768, [0.02] * 768])
    mock.embed_query = AsyncMock(return_value=[0.05] * 768)
    mock.embed_documents = AsyncMock(return_value=[[0.05] * 768])
    return mock


# ============================================================================
# Mock Vector Search (Qdrant)
# ============================================================================

@pytest.fixture
def mock_qdrant() -> MagicMock:
    mock = MagicMock()
    mock.search = AsyncMock(return_value=[
        MagicMock(
            id="chunk-123",
            score=0.92,
            payload={
                "document_id": "doc-456",
                "page_number": 1,
                "chunk_index": 0,
                "text": "Machine learning supervised and unsupervised algorithms.",
            }
        )
    ])
    mock.upsert = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    return mock


# ============================================================================
# Mock Redis Cache
# ============================================================================

@pytest.fixture
def mock_redis() -> MagicMock:
    storage = {}
    mock = MagicMock()

    async def mock_get(key: str):
        return storage.get(key)

    async def mock_set(key: str, value: str, *args, **kwargs):
        storage[key] = value
        return True

    async def mock_delete(key: str):
        if key in storage:
            del storage[key]
            return 1
        return 0

    async def mock_exists(key: str):
        return 1 if key in storage else 0

    mock.get = AsyncMock(side_effect=mock_get)
    mock.set = AsyncMock(side_effect=mock_set)
    mock.delete = AsyncMock(side_effect=mock_delete)
    mock.exists = AsyncMock(side_effect=mock_exists)
    return mock


@pytest.fixture(autouse=True)
def auto_mock_redis_client():
    from app.core.redis import redis_client
    with patch.object(redis_client, "get", new_callable=AsyncMock) as mock_get, \
         patch.object(redis_client, "set", new_callable=AsyncMock) as mock_set, \
         patch.object(redis_client, "delete", new_callable=AsyncMock) as mock_delete, \
         patch.object(redis_client, "exists", new_callable=AsyncMock) as mock_exists, \
         patch.object(redis_client, "increment", new_callable=AsyncMock) as mock_incr, \
         patch.object(redis_client, "expire", new_callable=AsyncMock) as mock_expire:
        mock_get.return_value = None
        mock_set.return_value = True
        mock_delete.return_value = True
        mock_exists.return_value = False
        mock_incr.return_value = 1
        mock_expire.return_value = True
        yield

