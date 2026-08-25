import pytest

from app.common.exceptions.database import DatabaseException
from app.common.exceptions.storage import FileStorageException
from app.common.utils.file import get_extension, get_filename
from app.common.utils.pagination import paginate
from app.common.utils.string import generate_uuid, normalize_string
from app.modules.chat.chat_session_model import ChatSessionDocument
from app.modules.document_chunks.schema import DocumentChunkResponse
from app.modules.document_contents.schema import DocumentContentResponse


def test_file_utils():
    assert get_extension("sample.PDF") == ".pdf"
    assert get_filename("/path/to/invoice.docx") == "invoice"


def test_pagination_utils():
    skip, limit = paginate(page=2, limit=10)
    assert skip == 10
    assert limit == 10

    skip, limit = paginate(page=1, limit=20)
    assert skip == 0
    assert limit == 20


def test_string_utils():
    u = generate_uuid()
    assert len(u) == 36
    assert normalize_string("  HELLO WORLD  ") == "hello world"


def test_custom_exceptions():
    d_exc = DatabaseException("DB error")
    assert d_exc.status_code == 500
    assert d_exc.message == "DB error"

    s_exc = FileStorageException("Storage error")
    assert s_exc.status_code == 500
    assert s_exc.message == "Storage error"


@pytest.mark.asyncio
async def test_router_helper():
    from app.common.router import health, router
    assert router.prefix == "/health"
    res = await health()
    assert res == {"status": "ok"}


def test_schemas_and_models():
    # ChatSessionDocument model
    session_doc = ChatSessionDocument(
        session_id="s123",
        document_id="d123",
    )
    assert session_doc.session_id == "s123"

    # Chunk schema
    chunk_resp = DocumentChunkResponse(
        document_id="doc_1",
        page_number=1,
        chunk_index=0,
        text="Some chunk text",
        token_count=5,
    )
    assert chunk_resp.document_id == "doc_1"

    # Content schema
    content_resp = DocumentContentResponse(
        document_id="doc_1",
        page_number=1,
        text="Page text content",
    )
    assert content_resp.document_id == "doc_1"
