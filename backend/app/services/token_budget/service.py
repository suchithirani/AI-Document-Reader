from collections import defaultdict


class TokenBudgetService:

    def __init__(
        self,
        max_characters: int = 5500,
    ):
        self.max_characters = max_characters

    def apply(
        self,
        results: list,
        ensure_document_coverage: bool = False,
        protected_pages: set[tuple[str, int]] | None = None,
    ):
        if not results:
            return []

        protected_pages = protected_pages or set()

        if protected_pages:
            return self._apply_with_protected_pages(
                results,
                protected_pages,
            )

        if ensure_document_coverage:
            return self._apply_with_document_coverage(
                results
            )

        return self._apply_normal(results)

    def _apply_normal(
        self,
        results: list,
    ):
        selected = []
        selected_keys = set()
        total = 0

        results = sorted(
            results,
            key=lambda item: item["score"],
            reverse=True,
        )

        for result in results:

            chunk = result["chunk"]

            key = self._chunk_key(chunk)

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


    def _apply_with_document_coverage(
        self,
        results: list,
    ):
        """
        Select representative evidence across the document.

        Strategy:
        1. Group chunks by document.
        2. Prefer high-quality chunks.
        3. Cover different pages first.
        4. Use remaining budget for additional
           high-scoring chunks.
        """

        grouped = defaultdict(list)

        for result in results:

            chunk = result["chunk"]

            grouped[
                chunk.document_id
            ].append(result)

        selected = []
        selected_keys = set()
        total = 0

        page_groups = defaultdict(list)

        for document_results in grouped.values():

            for result in document_results:

                chunk = result["chunk"]

                page_groups[
                    (
                        chunk.document_id,
                        chunk.page_number,
                    )
                ].append(result)

        best_per_page = []

        for page_results in page_groups.values():

            best = max(
                page_results,
                key=lambda item: item["score"],
            )

            best_per_page.append(best)

        # Highest quality pages first
        best_per_page.sort(
            key=lambda item: item["score"],
            reverse=True,
        )


        for result in best_per_page:

            chunk = result["chunk"]

            key = self._chunk_key(chunk)

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


        remaining = sorted(
            results,
            key=lambda item: item["score"],
            reverse=True,
        )

        for result in remaining:

            chunk = result["chunk"]

            key = self._chunk_key(chunk)

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


        selected.sort(
            key=lambda item: (
                item["chunk"].document_id,
                item["chunk"].page_number,
                item["chunk"].chunk_index,
            )
        )

        return selected



    def _apply_with_protected_pages(
        self,
        results: list,
        protected_pages: set[tuple[str, int]],
    ):
        """
        Explicitly requested pages are protected.

        All chunks from those pages are retained.
        Other pages use the normal budget.
        """

        protected = []
        normal = []

        for result in results:

            chunk = result["chunk"]

            page_key = (
                chunk.document_id,
                chunk.page_number,
            )

            if page_key in protected_pages:
                protected.append(result)
            else:
                normal.append(result)

        protected.sort(
            key=lambda item: (
                item["chunk"].document_id,
                item["chunk"].page_number,
                item["chunk"].chunk_index,
            )
        )

        selected = []
        selected_keys = set()

        # Requested pages first
        for result in protected:

            chunk = result["chunk"]

            key = self._chunk_key(chunk)

            if key in selected_keys:
                continue

            selected.append(result)
            selected_keys.add(key)

        total = sum(
            len(result["chunk"].text)
            for result in selected
        )

        # Remaining budget
        normal.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        for result in normal:

            chunk = result["chunk"]

            key = self._chunk_key(chunk)

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


    @staticmethod
    def _chunk_key(chunk):

        return (
            chunk.document_id,
            chunk.page_number,
            chunk.chunk_index,
        )