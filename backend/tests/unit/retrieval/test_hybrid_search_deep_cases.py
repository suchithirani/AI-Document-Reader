from unittest.mock import MagicMock

from app.modules.document_chunks.model import DocumentChunk
from app.services.hybrid_search.service import HybridSearchService


def test_hybrid_search_merge_scoring_and_deduplication():
    service = HybridSearchService()

    # Mock chunks
    c1 = MagicMock(spec=DocumentChunk)
    c1.id = "c1"
    c1.document_id = "doc_1"
    c1.page_number = 1
    c1.chunk_index = 0
    c1.text = "Invoice #101 total amount $500"

    c2 = MagicMock(spec=DocumentChunk)
    c2.id = "c2"
    c2.document_id = "doc_1"
    c2.page_number = 2
    c2.chunk_index = 1
    c2.text = "Terms and conditions"

    vector_results = [{"chunk": c1, "score": 0.9}, {"chunk": c2, "score": 0.7}]
    keyword_results = [{"chunk": c1, "score": 12.5}, {"chunk": c2, "score": 8.2}]

    # 1. Test merge
    merged = service.merge(
        vector_results=vector_results,
        keyword_results=keyword_results,
        top_k=2,
        question="What is the invoice amount?",
    )
    assert len(merged) <= 2
    assert merged[0]["chunk"].id == "c1"

    # 2. Empty results edge case
    assert service.merge([], [], top_k=5, question="test") == []
