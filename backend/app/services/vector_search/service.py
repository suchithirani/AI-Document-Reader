import math


class VectorSearchService:

    MIN_SCORE = 0.65

    def cosine_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float],
    ) -> float:

        dot = sum(
            a * b
            for a, b in zip(
                embedding1,
                embedding2,
            )
        )

        norm1 = math.sqrt(
            sum(
                a * a
                for a in embedding1
            )
        )

        norm2 = math.sqrt(
            sum(
                b * b
                for b in embedding2
            )
        )

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    def search(
        self,
        query_embedding: list[float],
        chunks,
        top_k: int = 5,
    ):

        scored_chunks = []

        for chunk in chunks:

            score = self.cosine_similarity(
                query_embedding,
                chunk.embedding,
            )

            # if score >= self.MIN_SCORE:

            scored_chunks.append(
                {
                    "score": score,
                    "chunk": chunk,
                }
            )

        scored_chunks.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return scored_chunks[:top_k]