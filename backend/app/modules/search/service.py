import asyncio
import json
import logging
from app.common.constants import QueryIntent
from collections import defaultdict
import re
from app.common.exceptions.auth import BaseAppException
from app.common.exceptions.search import SearchException
from app.modules.document_chunks.service import DocumentChunkService
from app.modules.document_images.service import DocumentImageService
from app.modules.documents.repository import DocumentRepository
from app.services.ai.service import AIService
from app.services.ocr_cleaner.service import clean_ocr_text
from app.services.analytics.ai_usage import AIUsageService
from app.services.bm25_search.service import BM25SearchService
from app.services.cache.embedding_cache import EmbeddingCache
from app.services.citation_validator.service import CitationValidator
from app.services.context_compressor.service import ContextCompressor
from app.services.embedding.service import EmbeddingService
from app.core.config import settings
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

BATCH_EXTRACTION_PROMPT = """You are a precise data extraction AI. Extract the following fields from the provided document texts.

For each document listed in the context, extract its fields and return them as an object in a JSON list. If a field is not explicitly present or readable in a document, return "N/A" for that field. Never guess or infer values from context.

JSON Schema per document item:
{{
  "document_id": "The exact ID of the document (provided in the XML tags)",
  "invoice_number": "Exact invoice number or ID",
  "date": "Date in DD/MM/YYYY format",
  "supplier": "Name of the selling/issuing company",
  "buyer": "Name of the customer (often listed after M/s. or Billed To)",
  "place_of_supply": "State and code (e.g. Gujarat (24))",
  "gstin": "15-character GSTIN code of the supplier (or buyer if supplier is missing)",
  "subtotal": "Subtotal numerical value (e.g. 9245.50)",
  "total_gst": "Total GST amount. If CGST and SGST are listed separately, sum them together.",
  "grand_total": "Grand total / Bill Amount / Total Payable numerical value",
  "main_products": "Name and description of main products listed",
  "quantity": "Total quantity or item count",
  "bank_details": "Bank account number and name if listed"
}}

Strict rules:
1. Do not cross-contaminate. Only extract values for document X using text located strictly inside the `<document id="X">...</document>` tags. Never copy values between different documents.
2. If text contains "Bill Amount: Nine Thousand Two Hundred Twenty Two Only", convert this word-form number to a digit: 9222.0
3. If CGST = 219.59 and SGST = 219.59, sum them and return 439.18 for "total_gst".

Document Contexts:
{context}

Response (Strictly valid JSON list of objects matching schema only):"""


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

        self.embedding_service = EmbeddingService(settings.EMBEDDING_PROVIDER)

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
        owner_id: str,
        document_ids: list[str] = None,
    ) -> list[dict]:

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

    async def _search_per_document(
        self,
        question: str,
        query_embedding: list[float],
        chunks: list,
        top_k: int,
        owner_id: str,
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

        for document_id, document_chunks in grouped_chunks.items():

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
                    owner_id=owner_id,
                    document_ids=[document_id],
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
            scopes = ["GLOBAL"]
            q_lower = question.lower()
            if any(term in q_lower for term in ["size", "type", "page count", "pages", "status", "created", "uploaded", "filename", "file name"]):
                scopes.insert(0, "METADATA")
            return scopes

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

            # Strip markdown fences
            if raw_answer.startswith("```"):
                raw_answer = re.sub(r"```(?:json)?", "", raw_answer).strip()

            # Extract the first JSON object robustly — handles extra text before/after
            json_match = re.search(r"\{.*?\}", raw_answer, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in scope planning response.")
            result = json.loads(json_match.group())

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

        except Exception as exception:

            logger.exception(
                "Retrieval scope planning failed.",
            )

            return ["GLOBAL"]

    async def _filter_chunks_by_pages(
        self,
        chunks: list,
        document_ids: list[str],
        pages: list[int],
    ) -> list:

        return [
            chunk
            for chunk in chunks
            if (
                chunk.document_id in document_ids
                and chunk.page_number in pages
            )
        ]

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
        documents: list[dict] = None,
    ) -> str:

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

            doc_name_map = {}
            if documents:
                doc_name_map = {doc["document_id"]: doc["document_name"] for doc in documents}

            for result in results:

                chunk = result["chunk"]

                cleaned_text = clean_ocr_text(chunk.text)
                doc_name = doc_name_map.get(chunk.document_id) or getattr(chunk, "document_name", None) or "Unknown Document"

                context += (
                    f"[SOURCE_{result['source_id']}]\n"
                    f"Document: "
                    f"{doc_name}\n"
                    f"Page: "
                    f"{chunk.page_number}\n"
                    f"Chunk: "
                    f"{chunk.chunk_index}\n"
                    f"Content:\n"
                    f"{cleaned_text}\n\n"
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

            intent_str = str(query_analysis.intent).lower()
            if len(document_ids) > 1 and intent_str in ("comparison", "summary", "general"):
                logger.info("Multi-document comparison/synthesis request. Redirecting to Isolation Extraction Pipeline.")
                md_table, metadata_sources, content_sources = await self._run_extraction_pipeline(
                    document_ids=document_ids,
                    question=question,
                    owner_id=owner_id
                )
                all_sources = {
                    "metadata": metadata_sources,
                    "content": content_sources
                }
                
                context = f"=== CONSOLIDATED DOCUMENT RECORDS ===\n\n{md_table}\n\n"
                prompt = self.prompt_builder.build(
                    history=history or [],
                    summary=summary,
                    context=context,
                    question=question,
                    intent=query_analysis.intent,
                    doc_types=["invoice"]
                )
                
                response = await self.ai_service.answer_question(prompt=prompt)
                answer = response["answer"]
                answer = self.citation_validator.validate(answer=answer, sources=content_sources)
                
                return {
                    "answer": answer,
                    "sources": all_sources
                }

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

            documents = (
                await self._get_document_metadata(
                    document_ids
                )
            )

            if "METADATA" in retrieval_scopes:

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
                    .get_chunks(
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

            filtered_chunks = []
            if "GLOBAL" in retrieval_scopes or "PER_DOCUMENT" in retrieval_scopes:
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

            if "GLOBAL" in retrieval_scopes:

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
                        owner_id=owner_id,
                        document_ids=document_ids,
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
                        owner_id=owner_id,
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

            intent_str = str(query_analysis.intent).lower()

            # =========================================================================
            # Special handling for Multi-Document Synthesis (Multi-RAG)
            # =========================================================================
            if (intent_str in ("summary", "comparison", "general") or getattr(query_analysis, "intent", None) in ("SUMMARY", "COMPARISON", "GENERAL")) and len(document_ids) > 1:
                logger.info("Multi-Document Synthesis triggered for %d documents (Intent: %s).", len(document_ids), intent_str)
                
                baseline_chunks = []
                doc_baselines = []
                for doc_id in document_ids:
                    doc_baseline = [c for c in chunks if c.document_id == doc_id and c.page_number == 1]
                    doc_baseline.sort(key=lambda x: x.chunk_index)
                    doc_baselines.append(doc_baseline[:3])
                
                # Interleave chunks: chunk0 from doc1, chunk0 from doc2... then chunk1...
                for i in range(3):
                    for db in doc_baselines:
                        if i < len(db):
                            baseline_chunks.append(db[i])
                
                logger.info("Extracted %d baseline chunks across all documents.", len(baseline_chunks))
                
                # Ensure no duplicates in results
                baseline_chunk_ids = {id(c) for c in baseline_chunks}
                filtered_results = [r for r in results if id(r["chunk"]) not in baseline_chunk_ids]
                
                baseline_results = [
                    {"chunk": c, "score": 1.0 - (i * 0.001)}
                    for i, c in enumerate(baseline_chunks)
                ]
                
                results = baseline_results + filtered_results

            # =========================================================================
            # Special handling for Table of Contents (TOC) queries to maintain continuity
            # =========================================================================
            original_max_chars = self.token_budget_service.max_characters
            # Increase budget for comprehensive summaries, comparisons, or TOC extraction (safe for free-tier rate limits)
            if intent_str in ("toc", "summary", "comparison", "general") or getattr(query_analysis, "intent", None) in ("TOC", "SUMMARY", "COMPARISON", "GENERAL"):
                self.token_budget_service.max_characters = 5000
                logger.info("Increased token budget limit to 5000 characters for intent: %s", intent_str)
            
            if (intent_str == "toc" or query_analysis.intent == QueryIntent.TOC) and results:
                logger.info("TOC intent matched successfully. Pulling full sequential pages.")
                toc_page = None
                toc_doc_id = None
                
                # 1. Identify the likely start page of the TOC
                for r in results:
                    c = r["chunk"]
                    t_lower = c.text.lower()
                    if "table of contents" in t_lower or "contents" in t_lower or "index" in t_lower:
                        toc_page = c.page_number
                        toc_doc_id = c.document_id
                        break
                
                if toc_page is None:
                    # Fallback to the top-scoring chunk's page
                    toc_page = results[0]["chunk"].page_number
                    toc_doc_id = results[0]["chunk"].document_id
                
                logger.info("TOC start page identified: Page %s in document %s", toc_page, toc_doc_id)
                
                # 2. Extract all chunks for the TOC start page and the subsequent page
                toc_chunks = [
                    c for c in chunks
                    if c.document_id == toc_doc_id and c.page_number in (toc_page, toc_page + 1)
                ]
                
                logger.info("Extracted %d chunks for sequential pages %s and %s", len(toc_chunks), toc_page, toc_page + 1)
                
                # 3. Sort them sequentially by page and chunk index to maintain reading order
                toc_chunks.sort(key=lambda x: (x.page_number, x.chunk_index))
                
                # 4. Replace results with these ordered chunks
                results = [
                    {"chunk": c, "score": 1.0 - (i * 0.01)}
                    for i, c in enumerate(toc_chunks)
                ]
                logger.info("Replaced results list with sequential TOC chunks.")
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
                self.token_budget_service.max_characters = original_max_chars
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
                documents=documents,
            )

            timer.start("Prompt Build")

            # Detect document types dynamically based on query and document names/metadata
            doc_types = set()
            for doc in (documents or []):
                name_lower = doc.get("document_name", "").lower()
                mime_lower = doc.get("mime_type", "").lower()
                if any(x in name_lower for x in ["invoice", "bill", "receipt", "payment"]):
                    doc_types.add("invoice")
                elif mime_lower in ["image/png", "image/jpeg"]:
                    doc_types.add("invoice")

            question_lower = question.lower()
            if any(x in question_lower for x in ["invoice", "bill", "receipt", "payment", "gst", "tax", "amount", "total"]):
                doc_types.add("invoice")

            prompt = self.prompt_builder.build(
                history=history or [],
                summary=summary,
                context=context,
                question=question,
                intent=query_analysis.intent,
                doc_types=list(doc_types),
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
                    "document_name": getattr(
                        result["chunk"],
                        "document_name",
                        None
                    ) or next(
                        (doc["document_name"] for doc in documents if doc["document_id"] == result["chunk"].document_id),
                        "Unknown Document"
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

    async def _run_extraction_pipeline(
        self,
        document_ids: list[str],
        question: str,
        owner_id: str,
    ) -> tuple[str, list[dict], list[dict]]:
        # 1. Fetch document metadata
        documents = await self._get_document_metadata(document_ids)
        metadata_sources = [
            {**doc, "source_type": "metadata"} for doc in documents
        ]
        
        # 2. Fetch all chunks
        chunks = await self.chunk_service.get_chunks(document_ids)
        
        # Group chunks by document_id
        chunks_by_doc = defaultdict(list)
        for chunk in chunks:
            chunks_by_doc[chunk.document_id].append(chunk)
            
        # 3. Batch Extraction per Document in 1 API Call using Gemini Flash (to support 50+ docs concurrently in <3s)
        from app.services.ai.providers.gemini import GeminiAIService
        gemini_extractor = GeminiAIService()
        doc_names = {doc["document_id"]: doc["document_name"] for doc in documents}
        
        # Build batch text context
        batch_context = ""
        print("\n========== ISOLATION EXTRACTION CHUNKS ==========")
        for doc_id in document_ids:
            doc_name = doc_names.get(doc_id, "Unknown Document")
            doc_chunks = chunks_by_doc.get(doc_id, [])
            doc_chunks.sort(key=lambda x: (x.page_number, x.chunk_index))
            print(f"Document: {doc_name} (ID: {doc_id}) | Chunks count: {len(doc_chunks)}")
            batch_context += f'<document id="{doc_id}">\n'
            for c in doc_chunks:
                cleaned = clean_ocr_text(c.text)
                batch_context += f"[PAGE_{c.page_number}_CHUNK_{c.chunk_index}]\n{cleaned}\n\n"
            batch_context += f'</document>\n\n'
        print("==================================================\n")
            
        prompt = BATCH_EXTRACTION_PROMPT.format(context=batch_context)
        
        raw_json = "[]"
        try:
            logger.info("Executing Batch Structured Extraction for %d documents in a single Gemini API call...", len(document_ids))
            response = await gemini_extractor.answer_question(prompt=prompt, model="gemini-3.6-flash")
            raw_json = response.get("answer", "")
        except Exception as e:
            logger.error("Failed batch structured extraction on Gemini Flash: %s", e)
            
        import re, json
        # Strip markdown formatting
        cleaned_json = raw_json.strip()
        if cleaned_json.startswith("```"):
            cleaned_json = re.sub(r"^```(?:json)?", "", cleaned_json).strip()
            cleaned_json = re.sub(r"```$", "", cleaned_json).strip()
            
        parsed_list = []
        try:
            parsed_list = json.loads(cleaned_json)
        except Exception:
            # Fallback search for JSON array block
            array_match = re.search(r"\[\s*\{.*\}\s*\]", raw_json, re.DOTALL)
            if array_match:
                try:
                    parsed_list = json.loads(array_match.group(0))
                except Exception:
                    pass
                    
        extracted_map = {}
        if isinstance(parsed_list, list):
            for item in parsed_list:
                if isinstance(item, dict) and "document_id" in item:
                    extracted_map[item["document_id"]] = item
                    
        # 4. Numerical Validation & Record Building
        records = []
        content_sources = []
        source_counter = 1
        
        for doc_id in document_ids:
            doc_name = doc_names.get(doc_id, "Unknown Document")
            data = extracted_map.get(doc_id, {})
            doc_chunks = chunks_by_doc.get(doc_id, [])
            doc_chunks.sort(key=lambda x: (x.page_number, x.chunk_index))
            
            # Mappings for citations
            doc_sources = []
            for chunk in doc_chunks[:2]: # Keep max 2 chunks to avoid citation bloating
                doc_sources.append(source_counter)
                content_sources.append({
                    "id": source_counter,
                    "document_name": doc_name,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "score": 1.0,
                    "snippet": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                    "source_type": "content"
                })
                source_counter += 1
                
            def clean_numeric(val):
                if not val or val == "N/A":
                    return 0.0, "N/A"
                cleaned = "".join(c for c in str(val) if c.isdigit() or c == ".")
                try:
                    return float(cleaned), val
                except ValueError:
                    return 0.0, val
                    
            subtotal_val, subtotal_str = clean_numeric(data.get("subtotal"))
            total_gst_val, total_gst_str = clean_numeric(data.get("total_gst"))
            grand_total_val, grand_total_str = clean_numeric(data.get("grand_total"))
            
            # Validation warnings
            warnings = []
            if subtotal_val > 0 and total_gst_val > 0 and grand_total_val > 0:
                if abs((subtotal_val + total_gst_val) - grand_total_val) > 2.0:
                    warnings.append("⚠️ Financial values inconsistent")
                    
            records.append({
                "document_name": doc_name,
                "invoice_number": data.get("invoice_number", "N/A"),
                "date": data.get("date", "N/A"),
                "supplier": data.get("supplier", "N/A"),
                "buyer": data.get("buyer", "N/A"),
                "place_of_supply": data.get("place_of_supply", "N/A"),
                "gstin": data.get("gstin", "N/A"),
                "subtotal": subtotal_str,
                "total_gst": total_gst_str,
                "grand_total": grand_total_str,
                "main_products": data.get("main_products", "N/A"),
                "quantity": data.get("quantity", "N/A"),
                "bank_details": data.get("bank_details", "N/A"),
                "warnings": ", ".join(warnings) if warnings else "OK",
                "citations": ", ".join(f"[{s}]" for s in doc_sources)
            })
            
        # 5. Build Markdown Table
        headers = [
            "Document", "Invoice Number", "Date", "Supplier", "Buyer", 
            "Place of Supply", "GSTIN", "Subtotal (₹)", "Total GST (₹)", 
            "Grand Total (₹)", "Main Products", "Quantity", "Bank Details", 
            "Validation Warnings", "Sources"
        ]
        
        md_table = "| " + " | ".join(headers) + " |\n"
        md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        for r in records:
            row = [
                r["document_name"], r["invoice_number"], r["date"], r["supplier"], r["buyer"],
                r["place_of_supply"], r["gstin"], r["subtotal"], r["total_gst"], r["grand_total"],
                r["main_products"], r["quantity"], r["bank_details"], r["warnings"], r["citations"]
            ]
            md_table += "| " + " | ".join(str(cell).replace("\n", " ").strip() for cell in row) + " |\n"
            
        return md_table, metadata_sources, content_sources

    async def search_stream(
        self,
        owner_id: str,
        session_id: str,
        document_ids: list[str],
        question: str,
        history: list | None = None,
        summary: str | None = None,
        top_k: int = 5,
    ):
        try:
            query_analysis = self.query_analyzer.analyze(question)
            intent_str = str(query_analysis.intent).lower()
            
            # If it's a multi-document comparison query, run extraction first
            if len(document_ids) > 1 and intent_str in ("comparison", "summary", "general"):
                md_table, metadata_sources, content_sources = await self._run_extraction_pipeline(
                    document_ids=document_ids,
                    question=question,
                    owner_id=owner_id
                )
                all_sources = {
                    "metadata": metadata_sources,
                    "content": content_sources
                }
                
                # Yield sources first so frontend gets them
                yield {"type": "sources", "content": all_sources}
                
                context = f"=== CONSOLIDATED DOCUMENT RECORDS ===\n\n{md_table}\n\n"
                prompt = self.prompt_builder.build(
                    history=history or [],
                    summary=summary,
                    context=context,
                    question=question,
                    intent=query_analysis.intent,
                    doc_types=["invoice"]
                )
                
                full_answer = ""
                async for chunk in self.ai_service.answer_question_stream(prompt=prompt):
                    full_answer += chunk
                    yield {"type": "chunk", "content": chunk}
                    
                yield {"type": "done", "content": full_answer}
                return

            # Fallback path for normal single-document queries
            explicit_pages = query_analysis.page_numbers
            is_broad_question = query_analysis.is_broad
            requires_images = query_analysis.requires_visual
            is_page_specific = (
                bool(explicit_pages)
                and query_analysis.scope == "page"
                and not is_broad_question
            )
            
            retrieval_scopes = await self._determine_retrieval_scopes(
                question=question,
                document_count=len(document_ids),
            )
            if is_broad_question and len(document_ids) > 1 and "PER_DOCUMENT" not in retrieval_scopes:
                retrieval_scopes.append("PER_DOCUMENT")
                
            retrieval_top_k = self.query_analyzer._get_retrieval_top_k(
                intent=query_analysis.intent,
                is_broad=query_analysis.is_broad,
                scope=query_analysis.scope,
            )
            
            metadata_context = ""
            metadata_sources = []
            documents = await self._get_document_metadata(document_ids)
            
            if "METADATA" in retrieval_scopes:
                metadata_context = "\n".join(
                    f"Document: {doc['document_name']}\nPage count: {doc['page_count']}\nFile size: {doc['file_size']}\nFile type: {doc['mime_type']}\nStatus: {doc['status']}\n"
                    for doc in documents
                )
                metadata_sources = [{**doc, "source_type": "metadata"} for doc in documents]
                
            query_embedding = None
            chunks = []
            results = []
            vision_results = []
            
            if "GLOBAL" in retrieval_scopes or "PER_DOCUMENT" in retrieval_scopes:
                query_embedding = await self.embedding_cache.get(question)
                if query_embedding is None:
                    query_embedding = await self.embedding_service.create_embedding(question)
                    await self.embedding_cache.set(question, query_embedding)
                    
                chunks = await self.chunk_service.get_chunks(document_ids)
                
            filtered_chunks = []
            if "GLOBAL" in retrieval_scopes or "PER_DOCUMENT" in retrieval_scopes:
                filtered_chunks = self.metadata_filter_service.filter(question=question, chunks=chunks)
                if is_page_specific:
                    filtered_chunks = self._filter_chunks_by_pages(chunks=filtered_chunks, document_ids=document_ids, pages=explicit_pages)
                    
            if "GLOBAL" in retrieval_scopes:
                results.extend(await self._search_global(question=question, query_embedding=query_embedding, chunks=filtered_chunks, top_k=retrieval_top_k, owner_id=owner_id, document_ids=document_ids))
                
            if "PER_DOCUMENT" in retrieval_scopes:
                results.extend(await self._search_per_document(question=question, query_embedding=query_embedding, chunks=filtered_chunks, top_k=retrieval_top_k, owner_id=owner_id))
                
            results = self._remove_duplicate_results(results)
            
            if is_page_specific:
                page_chunks = [c for c in chunks if c.document_id in document_ids and c.page_number in explicit_pages]
                existing_keys = {(r["chunk"].document_id, r["chunk"].page_number, r["chunk"].chunk_index) for r in results}
                for c in page_chunks:
                    if (c.document_id, c.page_number, c.chunk_index) not in existing_keys:
                        results.append({"chunk": c, "score": 0.0})
                        
            if requires_images:
                image_records = await self._retrieve_images(document_ids=document_ids, results=results, explicit_pages=explicit_pages, requires_images=requires_images)
                vision_results = await self._run_vision(images=image_records, question=question)
                
            results.sort(key=lambda item: item.get("score", 0.0), reverse=True)
            results = self._select_relevant_chunks(results=results, question=question, is_broad_question=is_broad_question)
            
            # Limit characters
            original_max_chars = self.token_budget_service.max_characters
            if intent_str in ("toc", "summary", "comparison", "general") or getattr(query_analysis, "intent", None) in ("TOC", "SUMMARY", "COMPARISON", "GENERAL"):
                self.token_budget_service.max_characters = 5000
                
            results = self.token_budget_service.apply(results, ensure_document_coverage=("PER_DOCUMENT" in retrieval_scopes), protected_pages={(d, p) for d in document_ids for p in explicit_pages})
            self.token_budget_service.max_characters = original_max_chars
            
            for source_id, result in enumerate(results, start=1):
                result["source_id"] = source_id
                
            context = self._build_context(results=results, metadata_context=metadata_context, vision_results=vision_results, documents=documents)
            
            doc_types = set()
            for doc in (documents or []):
                name_lower = doc.get("document_name", "").lower()
                mime_lower = doc.get("mime_type", "").lower()
                if any(x in name_lower for x in ["invoice", "bill", "receipt", "payment"]):
                    doc_types.add("invoice")
                elif mime_lower in ["image/png", "image/jpeg"]:
                    doc_types.add("invoice")
            if any(x in question.lower() for x in ["invoice", "bill", "receipt", "payment", "gst", "tax", "amount", "total"]):
                doc_types.add("invoice")
                
            prompt = self.prompt_builder.build(
                history=history or [],
                summary=summary,
                context=context,
                question=question,
                intent=query_analysis.intent,
                doc_types=list(doc_types),
            )
            
            content_sources = [
                {
                    "id": result["source_id"],
                    "document_name": getattr(result["chunk"], "document_name", None) or next((doc["document_name"] for doc in documents if doc["document_id"] == result["chunk"].document_id), "Unknown Document"),
                    "page_number": result["chunk"].page_number,
                    "chunk_index": result["chunk"].chunk_index,
                    "score": round(result["score"], 4),
                    "snippet": result["chunk"].text[:200] + "..." if len(result["chunk"].text) > 200 else result["chunk"].text,
                    "source_type": "content",
                }
                for result in results
            ]
            for vision in vision_results:
                if not vision.get("result"):
                    continue
                content_sources.append({
                    "id": vision["source_id"],
                    "document_name": vision["document_id"],
                    "page_number": vision["page_number"],
                    "chunk_index": None,
                    "score": None,
                    "snippet": vision["result"][:200] + "..." if len(vision["result"]) > 200 else vision["result"],
                    "source_type": "vision",
                })
                
            all_sources = {"metadata": metadata_sources, "content": content_sources}
            
            # Yield sources
            yield {"type": "sources", "content": all_sources}
            
            full_answer = ""
            async for chunk in self.ai_service.answer_question_stream(prompt=prompt):
                full_answer += chunk
                yield {"type": "chunk", "content": chunk}
                
            full_answer = self.citation_validator.validate(answer=full_answer, sources=content_sources)
            yield {"type": "done", "content": full_answer}
            
        except Exception as exception:
            logger.exception("Document search stream failed.")
            raise SearchException(str(exception)) from exception