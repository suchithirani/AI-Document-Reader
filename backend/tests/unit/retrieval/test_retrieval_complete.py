from unittest.mock import MagicMock

import pytest

from app.services.retrieval.service import RetrievalService


@pytest.mark.asyncio
async def test_retrieval_service_all_methods():
    mock_vector = MagicMock()
    mock_bm25 = MagicMock()
    mock_hybrid = MagicMock()

    retrieval = RetrievalService(
        vector_service=mock_vector,
        bm25_service=mock_bm25,
        hybrid_search_service=mock_hybrid,
    )

    chunks = [
        MagicMock(document_id="doc1", page_number=1, chunk_index=0, text="Table of Contents section"),
        MagicMock(document_id="doc1", page_number=1, chunk_index=1, text="Introduction and summary"),
        MagicMock(document_id="doc1", page_number=2, chunk_index=0, text="Details on page 2"),
        MagicMock(document_id="doc2", page_number=1, chunk_index=0, text="Doc 2 page 1 content"),
    ]

    # 1. filter_chunks_by_pages
    filtered = retrieval.filter_chunks_by_pages(chunks, document_ids=["doc1"], pages=[1])
    assert len(filtered) == 2
    assert all(c.document_id == "doc1" and c.page_number == 1 for c in filtered)

    # 2. sort_results
    results = [
        {"chunk": chunks[0], "score": 0.5},
        {"chunk": chunks[1], "score": 0.9},
        {"chunk": chunks[2], "score": 0.7},
    ]
    sorted_res = retrieval.sort_results(results)
    assert sorted_res[0]["score"] == 0.9

    # 3. remove_duplicate_results
    dup_results = [
        {"chunk": chunks[0], "score": 0.9},
        {"chunk": chunks[0], "score": 0.8},
        {"chunk": chunks[1], "score": 0.7},
    ]
    unique = retrieval.remove_duplicate_results(dup_results)
    assert len(unique) == 2

    # 4. include_page_chunks
    incl = retrieval.include_page_chunks(
        results=[{"chunk": chunks[0], "score": 0.9}],
        chunks=chunks,
        document_ids=["doc1"],
        pages=[1, 2],
    )
    assert len(incl) >= 2

    # 5. retrieve_toc_chunks
    toc_res = retrieval.retrieve_toc_chunks(results=[{"chunk": chunks[0], "score": 0.9}], chunks=chunks)
    assert len(toc_res) >= 1

    # 6. ensure_multi_document_coverage
    multi_cov = retrieval.ensure_multi_document_coverage(
        results=[],
        chunks=chunks,
        document_ids=["doc1", "doc2"],
        chunks_per_document=1,
    )
    assert len(multi_cov) >= 2

    # 7. select_relevant_chunks (Narrow & Broad)
    narrow = retrieval.select_relevant_chunks(results, is_broad_question=False)
    assert len(narrow) <= retrieval.MAX_FINAL_CHUNKS

    broad = retrieval.select_relevant_chunks(results, is_broad_question=True)
    assert len(broad) >= 1

    # 8. search_global & search_per_document
    mock_bm25.search.return_value = [{"chunk": chunks[0], "score": 5.0}]
    mock_vector.search.return_value = [{"chunk": chunks[0], "score": 0.9}]
    mock_hybrid.merge.return_value = [{"chunk": chunks[0], "score": 0.95}]

    global_res = await retrieval.search_global(
        question="test question",
        query_embedding=[0.1] * 768,
        chunks=chunks,
        top_k=5,
        owner_id="user1",
    )
    assert len(global_res) == 1

    per_doc_res = await retrieval.search_per_document(
        question="test question",
        query_embedding=[0.1] * 768,
        chunks=chunks,
        top_k=5,
        owner_id="user1",
    )
    assert len(per_doc_res) >= 1
