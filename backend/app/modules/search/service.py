import asyncio
import json
import logging
from collections import defaultdict
import re
from app.common.exceptions.auth import BaseAppException
from app.common.exceptions.search import SearchException
from app.modules.document_chunks.service import DocumentChunkService
from app.modules.document_images.service import DocumentImageService
from app.modules.documents.repository import DocumentRepository
from app.services.ai.service import AIService
from app.services.analytics.ai_usage import AIUsageService
from app.services.bm25_search.service import BM25SearchService
from app.services.cache.embedding_cache import EmbeddingCache
from app.services.citation_validator.service import CitationValidator
from app.services.context_compressor.service import ContextCompressor
from app.services.embedding.gemini import GeminiEmbedding
from app.services.hybrid_search.service import HybridSearchService
from app.services.image_query.service import ImageQueryService
from app.services.metadata_filter.service import MetadataFilterService
from app.services.page_query.service import PageQueryService
from app.services.performance_logger.service import PerformanceLogger
from app.services.prompt_builder.service import PromptBuilder
from app.services.token_budget.service import TokenBudgetService
from app.services.vector_search.service import VectorSearchService
from app.services.vision.service import VisionService
from app.services.query_analysis.analyzer import QueryAnalyzer
from app.common.constants import QueryIntent

logger = logging.getLogger(__name__)


class SearchService:

    BROAD_RETRIEVAL_TOP_K = 50
    VISUAL_PAGE_LIMIT = 5
    MULTI_PAGE_MIN_RESULTS = 10
    MAX_FINAL_CHUNKS = 8
    MAX_CHUNKS_PER_PAGE = 2
    PAGE_NEIGHBOR_WINDOW = 1
    MIN_RELATED_SCORE_RATIO = 0.70

    def __init__(self, db):

        self.chunk_service = DocumentChunkService(db)

        self.document_repository = DocumentRepository(db)

        self.embedding_service = GeminiEmbedding()

        self.embedding_cache = EmbeddingCache()

        self.vector_service = VectorSearchService()

        self.bm25_service = BM25SearchService()

        self.hybrid_search_service = (
            HybridSearchService()
        )

        self.metadata_filter_service = (
            MetadataFilterService()
        )

        self.context_compressor_service = (
            ContextCompressor()
        )

        self.token_budget_service = (
            TokenBudgetService()
        )

        self.prompt_builder = PromptBuilder()

        self.ai_service = AIService()

        self.ai_usage = AIUsageService(db)

        self.document_image_service = (
            DocumentImageService(db)
        )

        self.vision_service = VisionService(
            ai_service=self.ai_service,
            document_image_service=(
                self.document_image_service
            ),
        )

        self.image_query_service = (
            ImageQueryService()
        )

        self.page_query_service = (
            PageQueryService()
        )

        self.citation_validator = (
            CitationValidator()
        )

        self.query_analyzer = QueryAnalyzer()

    async def _determine_retrieval_scopes(
        self,
        question: str,
        document_count: int,
    ) -> list[str]:
        """
        Determine which retrieval scopes are required for a question.

        The decision is delegated to the AI planner because the uploaded
        documents may contain different types of information.
        """

        if document_count <= 1:
            return ["GLOBAL"]

        prompt = f"""
You are a retrieval planner for a generic AI document reader.

Return ONLY valid JSON:

{{
    "scopes": [
        "METADATA",
        "PER_DOCUMENT",
        "GLOBAL"
    ]
}}

Available scopes:

METADATA
- file name
- file type
- page count
- file size
- document status
- other document metadata

PER_DOCUMENT
- asks about each document individually
- asks for a summary or information from every document

GLOBAL
- asks about document content
- asks to find, explain, compare, or summarize information
- asks a question across the uploaded documents

Rules:

1. Return every required scope.
2. Do not duplicate scopes.
3. Use METADATA only when metadata is required.
4. Use PER_DOCUMENT when each document needs separate coverage.
5. Use GLOBAL for general content retrieval.
6. Multiple scopes are allowed.
7. Preserve this order:
   METADATA → PER_DOCUMENT → GLOBAL

Question:
{question}
"""

        try:
            response = await self.ai_service.answer_question(
                prompt=prompt,
            )

            raw_answer = response["answer"].strip()

            if raw_answer.startswith("```"):
                raw_answer = (
                    raw_answer
                    .replace("```json", "", 1)
                    .replace("```", "", 1)
                    .strip()
                )

            result = json.loads(raw_answer)

            valid_scopes = {
                "METADATA",
                "PER_DOCUMENT",
                "GLOBAL",
            }

            scopes = [
                scope
                for scope in result.get(
                    "scopes",
                    [],
                )
                if scope in valid_scopes
            ]

            return list(dict.fromkeys(scopes)) or [
                "GLOBAL"
            ]

        except Exception:
            logger.warning(
                "Retrieval scope planning failed; "
                "falling back to GLOBAL retrieval.",
                exc_info=True,
            )

            return ["GLOBAL"]

    def _filter_chunks_by_pages(
        self,
        chunks,
        document_ids: list[str],
        pages: list[int],
    ):
        """
        Restrict content retrieval to explicitly requested pages.
        """

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

    def _get_relevant_pages(
        self,
        results: list[dict],
        document_ids: list[str],
        limit: int = 5,
    ) -> dict[str, list[int]]:
        """
        Collect the most relevant pages from retrieval results.

        Pages are grouped by document so visual retrieval can request
        multiple relevant pages without losing document boundaries.
        """

        page_scores = defaultdict(dict)

        for result in results:

            chunk = result["chunk"]

            document_id = chunk.document_id
            page_number = chunk.page_number
            score = result.get("score", 0.0)

            current_score = page_scores[
                document_id
            ].get(
                page_number,
                float("-inf"),
            )

            page_scores[
                document_id
            ][page_number] = max(
                current_score,
                score,
            )

        relevant_pages = {}

        for document_id, pages in page_scores.items():

            sorted_pages = sorted(
                pages.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            relevant_pages[document_id] = [
                page_number
                for page_number, _ in sorted_pages[
                    :limit
                ]
            ]

        return relevant_pages

    async def _search_global(
        self,
        question: str,
        query_embedding: list[float],
        chunks: list,
        top_k: int,
    ) -> list[dict]:

        keyword_results = self.bm25_service.search(
            question=question,
            chunks=chunks,
            top_k=top_k,
        )

        vector_results = self.vector_service.search(
            query_embedding=query_embedding,
            chunks=chunks,
            top_k=top_k,
        )

        return self.hybrid_search_service.merge(
            vector_results=vector_results,
            keyword_results=keyword_results,
            top_k=top_k,
            question=question,
        )

    async def _search_per_document(
        self,
        question: str,
        query_embedding: list[float],
        chunks: list,
        top_k: int,
    ) -> list[dict]:

        grouped_chunks = defaultdict(list)

        for chunk in chunks:
            grouped_chunks[
                chunk.document_id
            ].append(chunk)

        results = []

        candidate_k = max(
            top_k * 2,
            10,
        )

        for document_chunks in grouped_chunks.values():

            keyword_results = (
                self.bm25_service.search(
                    question=question,
                    chunks=document_chunks,
                    top_k=candidate_k,
                )
            )

            vector_results = (
                self.vector_service.search(
                    query_embedding=query_embedding,
                    chunks=document_chunks,
                    top_k=candidate_k,
                )
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

    async def _get_document_metadata(
        self,
        document_ids: list[str],
    ) -> list[dict]:

        documents = []

        for document_id in document_ids:

            document = (
                await self.document_repository
                .get_document_by_id(
                    document_id,
                )
            )

            if document is None:
                continue

            documents.append(
                {
                    "document_id": document_id,
                    "document_name": (
                        document.original_filename
                    ),
                    "page_count": document.page_count,
                    "file_size": document.file_size,
                    "mime_type": document.mime_type,
                    "status": document.status,
                }
            )

        return documents

    def _select_relevant_chunks(
        self,
        results,
        question: str,
        is_broad_question: bool,
    ):
        """
        Reduce noisy retrieval results while preserving
        multi-page continuity.

        Strongly ranked pages are kept first.
        Nearby pages are allowed when they are part of
        the same document section.
        """

        if not results:
            return []

        # ---------------------------------------------------------
        # Sort by retrieval score
        # ---------------------------------------------------------

        ranked = sorted(
            results,
            key=lambda item: float(
                item.get("score", 0.0)
            ),
            reverse=True,
        )

        # Narrow factual questions:
        # don't introduce extra pages unnecessarily.
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

        # ---------------------------------------------------------
        # Broad / explanatory questions
        # ---------------------------------------------------------

        strongest_score = float(
            ranked[0].get("score", 0.0)
        )

        if strongest_score <= 0:
            return ranked[:self.MAX_FINAL_CHUNKS]

        minimum_score = (
            strongest_score
            * self.MIN_RELATED_SCORE_RATIO
        )

        # First collect strong pages.
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

        # ---------------------------------------------------------
        # Add neighboring pages.
        #
        # This is important for things like:
        # Page 38 -> Page 39
        #
        # where one page starts a section and the next
        # page contains its diagram/details.
        # ---------------------------------------------------------

        candidate_pages = set(
            strong_pages
        )

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

        # ---------------------------------------------------------
        # Select chunks from relevant pages
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Keep results ordered by document/page/chunk
        # rather than retrieval score.
        #
        # This makes multi-page context coherent.
        # ---------------------------------------------------------

        selected.sort(
            key=lambda item: (
                item["chunk"].document_id,
                item["chunk"].page_number,
                item["chunk"].chunk_index,
            )
        )

        return selected

    async def _retrieve_images(
        self,
        document_ids: list[str],
        results: list[dict],
        explicit_pages: list[int],
        requires_images: bool,
    ) -> list[dict]:

        if not requires_images:
            return []

        if explicit_pages:

            page_numbers = {
                document_id: explicit_pages
                for document_id in document_ids
            }

            return (
                await self.document_image_service
                .get_images_for_query(
                    document_ids=document_ids,
                    page_numbers=page_numbers,
                    limit=10,
                )
            )


        relevant_pages = self._get_relevant_pages(
            results=results,
            document_ids=document_ids,
            limit=self.VISUAL_PAGE_LIMIT,
        )

        if relevant_pages:

            images = (
                await self.document_image_service
                .get_images_for_query(
                    document_ids=document_ids,
                    page_numbers=relevant_pages,
                    limit=10,
                )
            )

            if images:
                return images

        return (
            await self.document_image_service
            .get_images_for_query(
                document_ids=document_ids,
                limit=10,
            )
        )

    async def _run_vision(
        self,
        images: list[dict],
        question: str,
    ) -> list[dict]:

        if not images:
            return []

        try:

            return (
                await self.vision_service
                .analyze_images_by_page(
                    images=images,
                    prompt=question,
                )
            )

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception(
                "Vision analysis failed."
            )

            return []

    def _remove_duplicate_results(
        self,
        results: list[dict],
    ) -> list[dict]:

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

    def _build_context(
        self,
        results: list[dict],
        metadata_context: str,
        vision_results: list[dict],
    ) -> None:

        context = ""

        if metadata_context:
            context += (
                "=== DOCUMENT METADATA ===\n"
                f"{metadata_context}\n\n"
            )

        if results:

            context += (
                "=== DOCUMENT CONTENT ===\n"
            )

            for result in results:

                chunk = result["chunk"]

                context += (
                    f"[SOURCE_{result['source_id']}]\n"
                    f"Document: "
                    f"{chunk.document_name}\n"
                    f"Page: "
                    f"{chunk.page_number}\n"
                    f"Chunk: "
                    f"{chunk.chunk_index}\n"
                    f"Content:\n"
                    f"{chunk.text}\n\n"
                )

        if vision_results:

            context += (
                "=== VISUAL INFORMATION ===\n"
            )

            source_id = len(results) + 1

            for result in vision_results:

                if not result.get("result"):
                    continue

                result["source_id"] = source_id

                context += (
                    f"[SOURCE_{source_id}]\n"
                    f"Document: "
                    f"{result['document_id']}\n"
                    f"Page: "
                    f"{result['page_number']}\n"
                    f"Content:\n"
                    f"{result['result']}\n\n"
                )

                source_id += 1

        return context

    async def search(
        self,
        owner_id: str,
        session_id: str,
        document_ids: list[str],
        question: str,
        history: list | None = None,
        summary: str | None = None,
        top_k: int = 5,
    ) -> dict:

        try:

            timer = PerformanceLogger()

            query_analysis = self.query_analyzer.analyze(
                question
            )

            is_broad_question = query_analysis.is_broad
            requires_images = query_analysis.requires_visual
            explicit_pages = query_analysis.page_numbers

            is_page_specific = (
                bool(explicit_pages)
                and query_analysis.scope == "page"
                and not is_broad_question
            )
            logger.info(
                "Query analysis: intent=%s scope=%s broad=%s visual=%s pages=%s",
                query_analysis.intent,
                query_analysis.scope,
                query_analysis.is_broad,
                query_analysis.requires_visual,
                query_analysis.page_numbers,
            )

            timer.start(
                "Retrieval Scope"
            )

            retrieval_scopes = (
                await self._determine_retrieval_scopes(
                    question=question,
                    document_count=len(
                        document_ids
                    ),
                )
            )

            timer.stop(
                "Retrieval Scope"
            )

            if (
                is_broad_question
                and len(document_ids) > 1
                and "PER_DOCUMENT"
                not in retrieval_scopes
            ):
                retrieval_scopes.append(
                    "PER_DOCUMENT"
                )

            retrieval_top_k = self.query_analyzer._get_retrieval_top_k(
                intent=query_analysis.intent,
                is_broad=query_analysis.is_broad,
                scope=query_analysis.scope,
            )

            metadata_context = ""
            metadata_sources = []
            documents = []
            chunks = []
            results = []
            vision_results = []

            if "METADATA" in retrieval_scopes:

                documents = (
                    await self._get_document_metadata(
                        document_ids
                    )
                )

                metadata_context = "\n".join(
                    (
                        f"Document: "
                        f"{document['document_name']}\n"
                        f"Page count: "
                        f"{document['page_count']}\n"
                        f"File size: "
                        f"{document['file_size']}\n"
                        f"File type: "
                        f"{document['mime_type']}\n"
                        f"Status: "
                        f"{document['status']}\n"
                    )
                    for document in documents
                )

                metadata_sources = [
                    {
                        **document,
                        "source_type": "metadata",
                    }
                    for document in documents
                ]

            query_embedding = None

            if (
                "GLOBAL" in retrieval_scopes
                or "PER_DOCUMENT"
                in retrieval_scopes
            ):

                timer.start("Embedding")

                query_embedding = (
                    await self.embedding_cache.get(
                        question
                    )
                )

                if query_embedding is None:

                    query_embedding = (
                        await self.embedding_service
                        .create_embedding(
                            question
                        )
                    )

                    await self.embedding_cache.set(
                        question,
                        query_embedding,
                    )

                timer.stop("Embedding")

                chunks = (
                    await self.chunk_service
                    .get_chunks_with_embeddings(
                        document_ids
                    )
                )
                if explicit_pages:

                    print("\n========== ALL DATABASE CHUNKS FOR REQUESTED PAGES ==========")

                    for page in explicit_pages:

                        page_chunks = [
                            chunk
                            for chunk in chunks
                            if (
                                chunk.document_id in document_ids
                                and chunk.page_number == page
                            )
                        ]

                        page_chunks.sort(
                            key=lambda chunk: chunk.chunk_index
                        )

                        print(
                            f"Page {page}: "
                            f"{len(page_chunks)} chunks"
                        )

                        for chunk in page_chunks:
                            print(
                                f"  chunk_index={chunk.chunk_index} "
                                f"tokens={getattr(chunk, 'token_count', '?')} "
                                f"text={chunk.text[:100]!r}"
                            )

                    print(
                        "============================================================\n"
                    )
                if explicit_pages:
                    print("\n========== REQUESTED PAGE DEBUG ==========")

                    for page in explicit_pages:
                        matching = [
                            chunk
                            for chunk in chunks
                            if (
                                chunk.document_id in document_ids
                                and chunk.page_number == page
                            )
                        ]

                        print(
                            f"Page {page}: "
                            f"{len(matching)} chunks"
                        )

                        print(
                            "Chunk indexes:",
                            [
                                chunk.chunk_index
                                for chunk in matching
                            ],
                        )

                    print("==========================================\n")

            if "GLOBAL" in retrieval_scopes:

                timer.start(
                    "Metadata Filter"
                )

                filtered_chunks = (
                    self.metadata_filter_service.filter(
                        question=question,
                        chunks=chunks,
                    )
                )

                if is_page_specific:
                    filtered_chunks = self._filter_chunks_by_pages(
                        chunks=filtered_chunks,
                        document_ids=document_ids,
                        pages=explicit_pages,
                    )

                timer.stop(
                    "Metadata Filter"
                )

                timer.start(
                    "Global Retrieval"
                )
                
                results.extend(
                    await self._search_global(
                        question=question,
                        query_embedding=(
                            query_embedding
                        ),
                        chunks=filtered_chunks,
                        top_k=retrieval_top_k,
                    )
                )

                timer.stop(
                    "Global Retrieval"
                )

            if "PER_DOCUMENT" in retrieval_scopes:

                timer.start(
                    "Per Document Retrieval"
                )

                results.extend(
                    await self._search_per_document(
                        question=question,
                        query_embedding=(
                            query_embedding
                        ),
                        chunks=filtered_chunks,
                        top_k=retrieval_top_k,
                    )
                )

                timer.stop(
                    "Per Document Retrieval"
                )

            results = (
                self._remove_duplicate_results(
                    results
                )
            )

            if is_page_specific:

                page_chunks = [
                    chunk
                    for chunk in chunks
                    if (
                        chunk.document_id
                        in document_ids
                        and chunk.page_number
                        in explicit_pages
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

            if requires_images:

                image_records = (
                    await self._retrieve_images(
                        document_ids=document_ids,
                        results=results,
                        explicit_pages=explicit_pages,
                        requires_images=requires_images,
                    )
                )

                vision_results = (
                    await self._run_vision(
                        images=image_records,
                        question=question,
                    )
                )

            results.sort(
                key=lambda item: item.get(
                    "score",
                    0.0,
                ),
                reverse=True,
            )

            results = self._select_relevant_chunks(
                results=results,
                question=question,
                is_broad_question=is_broad_question,
            )

            print(
                "========== FINAL SELECTED CHUNKS =========="
            )

            for result in results:

                chunk = result["chunk"]

                print(
                    f"Page {chunk.page_number} "
                    f"chunk={chunk.chunk_index} "
                    f"score={result.get('score')}"
                )

            print(
                "============================================"
            )

            if results:

                timer.start(
                    "Context Compressor"
                )

                results = (
                    self.context_compressor_service
                    .compress(results)
                )

                timer.stop(
                    "Context Compressor"
                )

                timer.start(
                    "Token Budget"
                )
                protected_pages = {
                    (
                        document_id,
                        page_number,
                    )
                    for document_id in document_ids
                    for page_number in explicit_pages
                }
                results = (
                    self.token_budget_service.apply(
                        results,
                        ensure_document_coverage=(
                            "PER_DOCUMENT"
                            in retrieval_scopes
                        ),protected_pages=protected_pages,
                    )
                )
                if explicit_pages:
                    print(
                        "\n========== EXPLICIT PAGE CONTEXT =========="
                    )

                    for page in explicit_pages:
                        page_chunks = [
                            result["chunk"]
                            for result in results
                            if result["chunk"].page_number == page
                        ]

                        print(
                            f"Page {page}: "
                            f"{len(page_chunks)} chunks"
                        )

                        print(
                            "Chunk indexes:",
                            [
                                chunk.chunk_index
                                for chunk in page_chunks
                            ],
                        )

                    print(
                        "===========================================\n"
                    )
                timer.stop(
                    "Token Budget"
                )

                for source_id, result in enumerate(
                    results,
                    start=1,
                ):
                    result["source_id"] = source_id

            if (
                not results
                and not metadata_context
                and not vision_results
            ):

                timer.print()

                return {
                    "answer": (
                        "I couldn't find relevant "
                        "information in the uploaded "
                        "documents."
                    ),
                    "sources": {
                        "metadata": metadata_sources,
                        "content": [],
                    },
                }

            context = self._build_context(
                results=results,
                metadata_context=metadata_context,
                vision_results=vision_results,
            )

            timer.start("Prompt Build")

            prompt = self.prompt_builder.build(
                history=history or [],
                summary=summary,
                context=context,
                question=question,
            )

            timer.stop("Prompt Build")

            timer.start("LLM")

            response = (
                await self.ai_service
                .answer_question(
                    prompt=prompt,
                )
            )

            answer = response["answer"]

            timer.stop("LLM")

            await self.ai_usage.log(
                user_id=owner_id,
                session_id=session_id,
                document_id=(
                    document_ids[0]
                    if len(document_ids) == 1
                    else None
                ),
                endpoint="chat",
                prompt_tokens=(
                    response["prompt_tokens"]
                ),
                completion_tokens=(
                    response["completion_tokens"]
                ),
                latency_ms=(
                    response["latency_ms"]
                ),
            )

            content_sources = [
                {
                    "id": result["source_id"],
                    "document_name": (
                        result["chunk"]
                        .document_name
                    ),
                    "page_number": (
                        result["chunk"]
                        .page_number
                    ),
                    "chunk_index": (
                        result["chunk"]
                        .chunk_index
                    ),
                    "score": round(
                        result["score"],
                        4,
                    ),
                    "snippet": (
                        result["chunk"].text[:200]
                        + "..."
                        if len(
                            result["chunk"].text
                        ) > 200
                        else result["chunk"].text
                    ),
                    "source_type": "content",
                }
                for result in results
            ]

            for vision in vision_results:

                if not vision.get("result"):
                    continue

                content_sources.append(
                    {
                        "id": vision["source_id"],
                        "document_name": (
                            vision["document_id"]
                        ),
                        "page_number": (
                            vision["page_number"]
                        ),
                        "chunk_index": None,
                        "score": None,
                        "snippet": (
                            vision["result"][:200]
                            + "..."
                            if len(
                                vision["result"]
                            ) > 200
                            else vision["result"]
                        ),
                        "source_type": "vision",
                    }
                )

            answer = (
                self.citation_validator.validate(
                    answer=answer,
                    sources=content_sources,
                )
            )

            timer.print()

            return {
                "answer": answer,
                "sources": {
                    "metadata": metadata_sources,
                    "content": content_sources,
                },
            }

        except SearchException:
            raise

        except BaseAppException:
            raise

        except Exception as exception:

            logger.exception(
                "Document search failed."
            )

            raise SearchException(
                str(exception)
            ) from exception