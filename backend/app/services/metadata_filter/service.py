class MetadataFilterService:

    def filter(
        self,
        question: str,
        chunks: list,
    ):

        question = question.lower()

        filtered = []

        for chunk in chunks:

            score = 0

            if (
                any(
                    char.isdigit()
                    for char in question
                )
                and chunk.has_numbers
            ):
                score += 1

            if (
                "email" in question
                and chunk.has_email
            ):
                score += 1

            if (
                "website" in question
                or "url" in question
                or "link" in question
            ) and chunk.has_url:
                score += 1

            if (
                "table" in question
                and chunk.has_table
            ):
                score += 1

            filtered.append(
                {
                    "chunk": chunk,
                    "score": score,
                }
            )

        filtered.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        if filtered and filtered[0]["score"] > 0:

            return [
                item["chunk"]
                for item in filtered
                if item["score"] > 0
            ]

        return chunks