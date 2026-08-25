from unittest.mock import MagicMock

from app.services.token_budget.service import TokenBudgetService


def test_token_budget_all_strategies():
    budget = TokenBudgetService(max_characters=800)

    chunk_p1 = MagicMock(document_id="doc1", page_number=1, chunk_index=0, text="A" * 200)
    chunk_p2 = MagicMock(document_id="doc1", page_number=2, chunk_index=0, text="B" * 200)
    chunk_p3 = MagicMock(document_id="doc1", page_number=3, chunk_index=0, text="C" * 200)
    chunk_p4 = MagicMock(document_id="doc2", page_number=1, chunk_index=0, text="D" * 200)

    results = [
        {"chunk": chunk_p1, "score": 0.9},
        {"chunk": chunk_p2, "score": 0.8},
        {"chunk": chunk_p3, "score": 0.7},
        {"chunk": chunk_p4, "score": 0.6},
    ]

    # 1. Normal Budget
    normal_sel = budget.apply(results)
    total_len = sum(len(r["chunk"].text) for r in normal_sel)
    assert total_len <= 800
    assert len(normal_sel) == 4

    # 2. Protected Pages
    prot_sel = budget.apply(
        results,
        protected_pages={("doc1", 3)},
    )
    assert any(r["chunk"].page_number == 3 for r in prot_sel)

    # 3. Document Coverage
    doc_cov_sel = budget.apply(
        results,
        ensure_document_coverage=True,
    )
    assert any(r["chunk"].document_id == "doc1" for r in doc_cov_sel)
    assert any(r["chunk"].document_id == "doc2" for r in doc_cov_sel)

    # 4. Empty results
    assert budget.apply([]) == []
