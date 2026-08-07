import re


class KeywordSearchService:

    def tokenize(
        self,
        text: str,
    ) -> list[str]:

        return re.findall(
            r"\b[a-zA-Z0-9]+\b",
            text.lower(),
        )

    def calculate_score(
        self,
        question: str,
        text: str,
    ) -> float:

        question_tokens = set(
            self.tokenize(question)
        )

        document_tokens = set(
            self.tokenize(text)
        )

        if not question_tokens:
            return 0.0

        matched = len(
            question_tokens.intersection(
                document_tokens
            )
        )

        return matched / len(question_tokens)

    def search(
        self,
        question: str,
        chunks,
        top_k: int = 5,
    ):

        scored_chunks = []

        for chunk in chunks:

            score = self.calculate_score(
                question,
                chunk.text,
            )

            if score > 0:

                scored_chunks.append(
                    {
                        "score": score,
                        "chunk": chunk,
                    }
                )

        scored_chunks.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return scored_chunks[:top_k]