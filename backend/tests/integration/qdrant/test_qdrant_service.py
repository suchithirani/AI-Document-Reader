from unittest.mock import MagicMock

from app.repositories.qdrant_repository import QdrantRepository


def test_qdrant_repository_initialization_and_search():
    repo = QdrantRepository()
    mock_client = MagicMock()
    repo.client = mock_client

    # Test upsert_chunks
    mock_chunk = MagicMock(
        id="6a8b2611d8bb8da18f059a3d",
        document_id="6a8b283fd8bb8da18f059a47",
        document_name="test.pdf",
        page_number=1,
        chunk_index=0,
        embedding=[0.1] * 768,
        text="sample text",
    )
    repo.upsert_chunks([mock_chunk], owner_id="user_123")
    assert mock_client.upsert.called
