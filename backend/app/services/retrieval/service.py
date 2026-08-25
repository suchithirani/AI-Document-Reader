import logging
from collections import defaultdict

from app.services.bm25_search.service import BM25SearchService
from app.services.hybrid_search.service import HybridSearchService
from app.services.vector_search.service import VectorSearchService

logger = logging.getLogger(__name__)

class RetrievalService:
    """
    Coordinates document retrieval using vector, BM25, and hybrid search.

    This service owns retrieval mechanics only.
    It does not:
    - generate embeddings
    - load chunks from the database
    - build prompts
    - call the LLM
    - perform vision analysis
    - generate citations
    """

    MAX_FINAL_CHUNKS = 8
    MAX_CHUNKS_PER_PAGE = 2
    PAGE_NEIGHBOR_WINDOW = 1
    MIN_RELATED_SCORE_RATIO = 0.70

    def __init__(
        self,
        vector_service: VectorSearchService | None = None,
        bm25_service: BM25SearchService | None = None,
        hybrid_search_service: HybridSearchService | None = None,
    ):
        self.vector_service = (
            vector_service or VectorSearchService()
        )

        self.bm25_service = (
            bm25_service or BM25SearchService()
        )

        self.hybrid_search_service = (
            hybrid_search_service or HybridSearchService()
        )

    def filter_chunks_by_pages(
        self,
        chunks: list,
        document_ids: list[str],
        pages: list[int],
    ) -> list:
        """Restrict chunks to explicitly requested pages."""

        if not pages:
            return chunks

        requested_pages = set(pages)
        requested_documents = set(document_ids)

        return [
            chunk
            for chunk in chunks
            if (
                chunk.document_id in requested_documents
                and chunk.page_number in requested_pages
            )
        ]

    def sort_results(
        self,
        results: list[dict],
    ) -> list[dict]:
        """Sort retrieval results by descending relevance score."""

        return sorted(
            results,
            key=lambda item: item.get("score", 0.0),
            reverse=True,
        )

    async def search_global(
        self,
        question: str,
        query_embedding: list[float],
        chunks: list,
        top_k: int,
        owner_id: str,
        document_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Perform global retrieval across all supplied chunks/documents.
        """

        keyword_results = self.bm25_service.search(
            question=question,
            chunks=chunks,
            top_k=top_k,
        )

        vector_results = self.vector_service.search(
            query_embedding=query_embedding,
            owner_id=owner_id,
            document_ids=document_ids,
            top_k=top_k,
        )

        return self.hybrid_search_service.merge(
            vector_results=vector_results,
            keyword_results=keyword_results,
            top_k=top_k,
            question=question,
        )

    async def search_per_document(
        self,
        question: str,
        query_embedding: list[float],
        chunks: list,
        top_k: int,
        owner_id: str,
    ) -> list[dict]:
        """
        Perform retrieval independently for each document.

        This prevents one document from dominating retrieval results
        when the user asks for per-document coverage.
        """

        grouped_chunks = defaultdict(list)

        for chunk in chunks:
            grouped_chunks[chunk.document_id].append(chunk)

        results = []

        candidate_k = max(
            top_k * 2,
            10,
        )

        for document_id, document_chunks in grouped_chunks.items():
            keyword_results = self.bm25_service.search(
                question=question,
                chunks=document_chunks,
                top_k=candidate_k,
            )

            vector_results = self.vector_service.search(
                query_embedding=query_embedding,
                owner_id=owner_id,
                document_ids=[document_id],
                top_k=candidate_k,
            )

            results.extend(
                self.hybrid_search_service.merge(
                    vector_results=vector_results,
                    keyword_results=keyword_results,
                    top_k=top_k,
                    question=question,
                )
            )

        return results

    def remove_duplicate_results(
        self,
        results: list[dict],
    ) -> list[dict]:
        """Remove duplicate chunks while preserving result order."""

        unique_results = []
        seen = set()

        for result in results:
            chunk = result["chunk"]

            key = (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,
            )

            if key in seen:
                continue

            seen.add(key)
            unique_results.append(result)

        return unique_results

    def include_page_chunks(
        self,
        results: list[dict],
        chunks: list,
        document_ids: list[str],
        pages: list[int],
    ) -> list[dict]:
        """
        Ensure all chunks from explicitly requested pages are included.

        Retrieved chunks keep their original relevance scores.
        Missing chunks are added with a neutral score of 0.0.
        """

        if not pages:
            return results

        requested_documents = set(document_ids)
        requested_pages = set(pages)

        page_chunks = [
            chunk
            for chunk in chunks
            if (
                chunk.document_id in requested_documents
                and chunk.page_number in requested_pages
            )
        ]

        existing_keys = {
            (
                result["chunk"].document_id,
                result["chunk"].page_number,
                result["chunk"].chunk_index,
            )
            for result in results
        }

        for chunk in page_chunks:

            key = (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,
            )

            if key in existing_keys:
                continue

            results.append(
                {
                    "chunk": chunk,
                    "score": 0.0,
                }
            )

        return results

    def retrieve_toc_chunks(
        self,
        results: list[dict],
        chunks: list,
    ) -> list[dict]:
        """
        Identify the table-of-contents page and return
        sequential chunks from the TOC page and the next page.
        """

        if not results:
            return []

        toc_page = None
        toc_document_id = None

        for result in results:

            chunk = result["chunk"]
            text_lower = chunk.text.lower()

            if (
                "table of contents" in text_lower
                or "contents" in text_lower
                or "index" in text_lower
            ):
                toc_page = chunk.page_number
                toc_document_id = chunk.document_id
                break

        if toc_page is None:

            toc_page = results[0]["chunk"].page_number
            toc_document_id = results[0]["chunk"].document_id

        toc_chunks = [
            chunk
            for chunk in chunks
            if (
                chunk.document_id == toc_document_id
                and chunk.page_number in (
                    toc_page,
                    toc_page + 1,
                )
            )
        ]

        toc_chunks.sort(
            key=lambda chunk: (
                chunk.page_number,
                chunk.chunk_index,
            )
        )

        return [
            {
                "chunk": chunk,
                "score": 1.0 - (index * 0.01),
            }
            for index, chunk in enumerate(toc_chunks)
        ]

    def ensure_multi_document_coverage(
        self,
        results: list[dict],
        chunks: list,
        document_ids: list[str],
        chunks_per_document: int = 3,
    ) -> list[dict]:
        """
        Ensure multi-document synthesis has baseline coverage
        from every requested document.

        Baseline chunks are taken from page 1 and interleaved
        across documents to prevent one document from dominating
        the context.
        """

        baseline_chunks = []

        for document_id in document_ids:

            document_chunks = [
                chunk
                for chunk in chunks
                if (
                    chunk.document_id == document_id
                    and chunk.page_number == 1
                )
            ]

            document_chunks.sort(
                key=lambda chunk: chunk.chunk_index
            )

            baseline_chunks.append(
                document_chunks[:chunks_per_document]
            )

        # Interleave documents.
        interleaved_chunks = []

        for index in range(chunks_per_document):

            for document_chunks in baseline_chunks:

                if index < len(document_chunks):
                    interleaved_chunks.append(
                        document_chunks[index]
                    )

        if not interleaved_chunks:
            return results

        baseline_keys = {
            (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,
            )
            for chunk in interleaved_chunks
        }

        filtered_results = [
            result
            for result in results
            if (
                result["chunk"].document_id,
                result["chunk"].page_number,
                result["chunk"].chunk_index,
            ) not in baseline_keys
        ]

        baseline_results = [
            {
                "chunk": chunk,
                "score": 1.0 - (index * 0.001),
            }
            for index, chunk in enumerate(
                interleaved_chunks
            )
        ]

        logger.info(
            "Added %d baseline chunks for multi-document coverage.",
            len(baseline_results),
        )

        return baseline_results + filtered_results

    def select_relevant_chunks(
        self,
        results: list[dict],
        is_broad_question: bool,
    ) -> list[dict]:
        """
        Reduce noisy retrieval results while preserving useful
        multi-page continuity.
        """

        if not results:
            return []

        ranked = sorted(
            results,
            key=lambda item: float(
                item.get("score", 0.0)
            ),
            reverse=True,
        )

        # Narrow factual questions.
        if not is_broad_question:
            selected = []
            seen = set()

            for result in ranked:
                chunk = result["chunk"]

                key = (
                    chunk.document_id,
                    chunk.page_number,
                    chunk.chunk_index,
                )

                if key in seen:
                    continue

                seen.add(key)
                selected.append(result)

                if len(selected) >= self.MAX_FINAL_CHUNKS:
                    break

            return selected

        # Broad / explanatory questions.
        strongest_score = float(
            ranked[0].get("score", 0.0)
        )

        if strongest_score <= 0:
            return ranked[:self.MAX_FINAL_CHUNKS]

        minimum_score = (
            strongest_score
            * self.MIN_RELATED_SCORE_RATIO
        )

        strong_pages = set()

        for result in ranked:
            score = float(
                result.get("score", 0.0)
            )

            if score < minimum_score:
                continue

            chunk = result["chunk"]

            strong_pages.add(
                (
                    chunk.document_id,
                    chunk.page_number,
                )
            )

        # Include neighboring pages for continuity.
        candidate_pages = set(strong_pages)

        for document_id, page_number in strong_pages:
            for offset in range(
                -self.PAGE_NEIGHBOR_WINDOW,
                self.PAGE_NEIGHBOR_WINDOW + 1,
            ):
                if offset == 0:
                    continue

                candidate_pages.add(
                    (
                        document_id,
                        page_number + offset,
                    )
                )

        selected = []
        page_counts = {}
        seen = set()

        for result in ranked:
            chunk = result["chunk"]

            page_key = (
                chunk.document_id,
                chunk.page_number,
            )

            chunk_key = (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,
            )

            if chunk_key in seen:
                continue

            if page_key not in candidate_pages:
                continue

            count = page_counts.get(
                page_key,
                0,
            )

            if count >= self.MAX_CHUNKS_PER_PAGE:
                continue

            selected.append(result)
            seen.add(chunk_key)

            page_counts[page_key] = count + 1

            if len(selected) >= self.MAX_FINAL_CHUNKS:
                break

        # Preserve document/page/chunk order for coherent context.
        selected.sort(
            key=lambda item: (
                item["chunk"].document_id,
                item["chunk"].page_number,
                item["chunk"].chunk_index,
            )
        )

        return selected
