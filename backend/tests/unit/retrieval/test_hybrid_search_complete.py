from unittest.mock import MagicMock

from app.services.hybrid_search.service import HybridSearchService


def test_hybrid_search_comprehensive_merge():
    service = HybridSearchService()

    chunk1 = MagicMock(document_id="doc1", page_number=1, chunk_index=0, text="Deep learning neural network architecture layers and loss optimization.")
    chunk2 = MagicMock(document_id="doc1", page_number=2, chunk_index=0, text="Support vector machines kernel trick classification.")
    chunk3 = MagicMock(document_id="doc2", page_number=1, chunk_index=0, text="Unrelated simple short noise.")

    vector_results = [
        {"chunk": chunk1, "score": 0.95},
        {"chunk": chunk2, "score": 0.80},
    ]

    keyword_results = [
        {"chunk": chunk1, "score": 12.5},
        {"chunk": chunk3, "score": 5.0},
    ]

    # 1. Normal targeted question
    merged = service.merge(
        vector_results=vector_results,
        keyword_results=keyword_results,
        top_k=2,
        question="What is deep learning neural network?",
    )

    assert len(merged) <= 2
    assert merged[0]["chunk"] == chunk1
    assert "phrase_score" in merged[0]
    assert "content_bonus" in merged[0]

    # 2. Broad question (triggers diversity reranking)
    broad_merged = service.merge(
        vector_results=vector_results,
        keyword_results=keyword_results,
        top_k=3,
        question="Give me an overall summary and main points of the entire document",
    )
    assert len(broad_merged) >= 1


def test_hybrid_search_edge_cases():
    service = HybridSearchService()

    # Empty inputs
    assert service.merge([], [], question="") == []

    # Single term query
    assert service._phrase_score("AI", "AI is great") == 0.0

    # Zero term query
    assert service._term_overlap_score("", "some text") == 0.0
    assert service._term_specificity("", ["some text"]) == {}
    assert service._weighted_overlap_score("", "some text", {}) == 0.0

    # Quality score check
    high_q = service._content_quality_score("This is a clean, well-formatted English sentence with good grammar and proper length.")
    low_q = service._content_quality_score("123 %%% $$$ @@@")
    assert high_q > low_q
