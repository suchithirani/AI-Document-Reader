class HybridSearchService:

    def __init__(
        self,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        bonus: float = 0.1,
    ):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.bonus = bonus

    def merge(
        self,
        vector_results: list,
        keyword_results: list,
        top_k: int = 5,
    ):

        merged = {}

        vector_max = max(
            [r["score"] for r in vector_results],
            default=1.0,
        )

        keyword_max = max(
            [r["score"] for r in keyword_results],
            default=1.0,
        )

        for result in vector_results:

            chunk = result["chunk"]

            key = (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,

            )

            merged[key] = {
                "chunk": chunk,
                "vector_score": (
                    result["score"] / vector_max
                ),
                "keyword_score": 0.0,
                "matched_by_vector": True,
                "matched_by_keyword": False,
            }

        for result in keyword_results:

            chunk = result["chunk"]

            key = (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,
            )

            keyword_score = (
                result["score"] / keyword_max
            )

            if key in merged:

                merged[key]["keyword_score"] = keyword_score
                merged[key]["matched_by_keyword"] = True

            else:

                merged[key] = {
                    "chunk": chunk,
                    "vector_score": 0.0,
                    "keyword_score": keyword_score,
                    "matched_by_vector": False,
                    "matched_by_keyword": True,
                }

        final_results = []

        for item in merged.values():

            score = (
                item["vector_score"]
                * self.vector_weight
            ) + (
                item["keyword_score"]
                * self.keyword_weight
            )

            if (
                item["matched_by_vector"]
                and item["matched_by_keyword"]
            ):
                score += self.bonus

            final_results.append(
                {
                    "chunk": item["chunk"],
                    "score": score,
                }
            )

        final_results.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return final_results[:top_k]