import re

from rank_bm25 import BM25Okapi


class BM25SearchService:

    def tokenize(
        self,
        text: str,
    ) -> list[str]:

        return re.findall(
            r"\b[a-zA-Z0-9]+\b",
            text.lower(),
        )

    def search(
        self,
        question: str,
        chunks,
        top_k: int = 5,
    ):

        if not chunks:
            return []

        corpus = [
            self.tokenize(
                chunk.text
            )
            for chunk in chunks
        ]

        bm25 = BM25Okapi(
            corpus,
        )

        query = self.tokenize(
            question,
        )

        scores = bm25.get_scores(
            query,
        )

        results = []

        for chunk, score in zip(
            chunks,
            scores,
        ):

            if score > 0:

                results.append(
                    {
                        "chunk": chunk,
                        "score": float(score),
                    }
                )

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return results[:top_k*3]