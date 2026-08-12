from collections import defaultdict


class TokenBudgetService:

    def __init__(
        self,
        max_characters: int = 8000,
    ):
        self.max_characters = max_characters

    def apply(
        self,
        results: list,
        ensure_document_coverage: bool = False,
    ):

        if not results:
            return []

        if not ensure_document_coverage:
            return self._apply_normal(results)

        return self._apply_with_document_coverage(
            results
        )

    def _apply_normal(
        self,
        results: list,
    ):

        selected = []
        total = 0

        for result in results:

            text = result["chunk"].text

            if (
                total + len(text)
                > self.max_characters
            ):
                break

            selected.append(result)

            total += len(text)

        return selected

    def _apply_with_document_coverage(
        self,
        results: list,
    ):

        grouped = defaultdict(list)

        for result in results:

            document_id = (
                result["chunk"].document_id
            )

            grouped[document_id].append(
                result
            )

        selected = []
        selected_keys = set()
        total = 0

        # ---------------------------------
        # First: one chunk per document
        # ---------------------------------
        for document_results in grouped.values():

            best_result = max(
                document_results,
                key=lambda item: item["score"],
            )

            text = best_result["chunk"].text

            if (
                total + len(text)
                > self.max_characters
            ):
                continue

            selected.append(best_result)

            selected_keys.add(
                (
                    best_result["chunk"].document_id,
                    best_result["chunk"].page_number,
                    best_result["chunk"].chunk_index,
                )
            )

            total += len(text)

        # ---------------------------------
        # Second: remaining best chunks
        # ---------------------------------
        remaining = sorted(
            results,
            key=lambda item: item["score"],
            reverse=True,
        )

        for result in remaining:

            chunk = result["chunk"]

            key = (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,
            )

            if key in selected_keys:
                continue

            text = chunk.text

            if (
                total + len(text)
                > self.max_characters
            ):
                continue

            selected.append(result)

            selected_keys.add(key)

            total += len(text)

        return selected