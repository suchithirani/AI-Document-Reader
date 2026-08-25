

def test_rag_retrieval_metrics():
    # Gold standard relevant document IDs for benchmark queries
    ground_truth = {"doc1", "doc2"}
    retrieved_results = ["doc1", "doc3", "doc2", "doc4"]

    # Precision@k (k=3)
    k = 3
    top_k = retrieved_results[:k]
    relevant_in_top_k = [doc for doc in top_k if doc in ground_truth]
    precision_at_k = len(relevant_in_top_k) / k

    # Recall@k (k=3)
    recall_at_k = len(relevant_in_top_k) / len(ground_truth)

    # Reciprocal Rank (RR)
    first_hit_rank = next(i + 1 for i, doc in enumerate(retrieved_results) if doc in ground_truth)
    reciprocal_rank = 1.0 / first_hit_rank

    assert precision_at_k >= 0.66
    assert recall_at_k == 1.0
    assert reciprocal_rank == 1.0  # Rank 1 hit


def test_citation_faithfulness_metric():
    answer = "Machine learning algorithms include Supervised and Unsupervised Learning [1]."
    sources = [{"id": 1, "text": "Supervised and Unsupervised Learning are core machine learning paradigms."}]

    # Faithfulness verification
    cited_id = 1
    cited_source = next((s for s in sources if s["id"] == cited_id), None)
    assert cited_source is not None
    assert "Supervised and Unsupervised" in cited_source["text"]
