from unittest.mock import MagicMock

from app.services.bm25_search.service import BM25SearchService
from app.services.context_compressor.service import ContextCompressor
from app.services.hybrid_search.service import HybridSearchService
from app.services.metadata_filter.service import MetadataFilterService
from app.services.token_budget.service import TokenBudgetService


def test_hybrid_search_tokenization_and_scoring():
    service = HybridSearchService()
    tokens = service._tokenize("Deep Learning with PyTorch!")
    assert "deep" in tokens
    assert "learning" in tokens
    assert "pytorch" in tokens

    terms = service._query_terms("What is the main concept of Deep Learning?")
    assert "deep" in terms
    assert "learning" in terms
    assert "what" not in terms


def test_hybrid_search_phrase_and_overlap_score():
    service = HybridSearchService()
    phrase_score = service._phrase_score(
        "machine learning algorithms",
        "This chapter covers machine learning algorithms and neural networks."
    )
    assert phrase_score > 0.5

    overlap = service._term_overlap_score(
        "machine learning",
        "Supervised machine learning algorithms"
    )
    assert overlap > 0.0


def test_bm25_search_scoring():
    service = BM25SearchService()
    chunks = [
        MagicMock(id="c1", text="Machine learning supervised classification"),
        MagicMock(id="c2", text="Deep neural networks convolutional layers"),
        MagicMock(id="c3", text="Unrelated text about cooking and food"),
    ]

    results = service.search(question="supervised machine learning", chunks=chunks, top_k=2)
    assert len(results) <= 2
    if results:
        assert results[0]["chunk"].id == "c1"


def test_metadata_filter_service():
    service = MetadataFilterService()

    chunks = [
        MagicMock(id="c1", has_numbers=True, has_email=False, has_url=False, has_table=False),
        MagicMock(id="c2", has_numbers=False, has_email=True, has_url=False, has_table=False),
        MagicMock(id="c3", has_numbers=False, has_email=False, has_url=False, has_table=False),
    ]

    # Filter by email keyword in question
    filtered = service.filter(question="What is the contact email address?", chunks=chunks)
    assert len(filtered) >= 1
    assert filtered[0].id == "c2"


def test_token_budget_service():
    budget = TokenBudgetService(max_characters=1000)

    chunks = [
        {"chunk": MagicMock(text="A" * 400), "score": 0.9},
        {"chunk": MagicMock(text="B" * 400), "score": 0.8},
        {"chunk": MagicMock(text="C" * 400), "score": 0.7},
    ]

    selected = budget.apply(chunks)
    total_chars = sum(len(item["chunk"].text) for item in selected)
    assert total_chars <= 1000
    assert len(selected) == 2


def test_context_compressor_service():
    compressor = ContextCompressor()

    results = [
        {
            "chunk": MagicMock(document_id="doc1", text="Duplicate text chunk content."),
            "score": 0.95
        },
        {
            "chunk": MagicMock(document_id="doc1", text="Duplicate text chunk content."),
            "score": 0.85
        },
        {
            "chunk": MagicMock(document_id="doc2", text="Different text chunk content."),
            "score": 0.75
        }
    ]

    compressed = compressor.compress(results)
    assert len(compressed) == 2
