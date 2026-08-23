import asyncio
import json
import logging
from collections import defaultdict
import re
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
from app.services.retrieval.service import RetrievalService
from app.common.exceptions.auth import BaseAppException

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


    def __init__(self, db):
        self.db = db
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

        self.retrieval_service = RetrievalService(
            vector_service=self.vector_service,
            bm25_service=self.bm25_service,
            hybrid_search_service=self.hybrid_search_service,
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

    async def _retrieve_context(
        self,
        question: str,
        document_ids: list[str],
        owner_id: str,
        query_analysis,
    ) -> dict:
        """
        Shared retrieval pipeline used by both search() and search_stream().

        Responsible only for:
        - retrieval scope determination
        - embedding generation
        - chunk loading
        - metadata filtering
        - global/per-document retrieval
        - page filtering
        - deduplication
        - relevance selection

        Does not handle:
        - vision
        - prompt building
        - LLM calls
        - citations
        - streaming
        """

        is_broad_question = query_analysis.is_broad
        explicit_pages = query_analysis.page_numbers

        is_page_specific = (
            bool(explicit_pages)
            and query_analysis.scope == "page"
            and not is_broad_question
        )

        # ---------------------------------------------------------
        # 1. Determine retrieval scopes
        # ---------------------------------------------------------

        retrieval_scopes = await self._determine_retrieval_scopes(
            question=question,
            document_count=len(document_ids),
        )

        if (
            is_broad_question
            and len(document_ids) > 1
            and "PER_DOCUMENT" not in retrieval_scopes
        ):
            retrieval_scopes.append("PER_DOCUMENT")

        # ---------------------------------------------------------
        # 2. Determine retrieval depth
        # ---------------------------------------------------------

        retrieval_top_k = self.query_analyzer._get_retrieval_top_k(
            intent=query_analysis.intent,
            is_broad=query_analysis.is_broad,
            scope=query_analysis.scope,
        )

        # ---------------------------------------------------------
        # 3. Load document metadata
        # ---------------------------------------------------------

        documents = await self._get_document_metadata(
            document_ids
        )

        metadata_context = ""
        metadata_sources = []

        if "METADATA" in retrieval_scopes:

            metadata_context = "\n".join(
                (
                    f"Document: {document['document_name']}\n"
                    f"Page count: {document['page_count']}\n"
                    f"File size: {document['file_size']}\n"
                    f"File type: {document['mime_type']}\n"
                    f"Status: {document['status']}\n"
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

        # ---------------------------------------------------------
        # 4. Embedding
        # ---------------------------------------------------------

        query_embedding = None

        if (
            "GLOBAL" in retrieval_scopes
            or "PER_DOCUMENT" in retrieval_scopes
        ):

            query_embedding = await self.embedding_cache.get(
                question
            )

            if query_embedding is None:

                query_embedding = (
                    await self.embedding_service.create_embedding(
                        question
                    )
                )

                await self.embedding_cache.set(
                    question,
                    query_embedding,
                )

        # ---------------------------------------------------------
        # 5. Load chunks
        # ---------------------------------------------------------

        chunks = []

        if (
            "GLOBAL" in retrieval_scopes
            or "PER_DOCUMENT" in retrieval_scopes
        ):
            chunks = await self.chunk_service.get_chunks(
                document_ids
            )

        # ---------------------------------------------------------
        # 6. Metadata filtering
        # ---------------------------------------------------------

        filtered_chunks = []

        if (
            "GLOBAL" in retrieval_scopes
            or "PER_DOCUMENT" in retrieval_scopes
        ):

            filtered_chunks = (
                self.metadata_filter_service.filter(
                    question=question,
                    chunks=chunks,
                )
            )

            if is_page_specific:

                filtered_chunks = (
                    self.retrieval_service.filter_chunks_by_pages(
                        chunks=filtered_chunks,
                        document_ids=document_ids,
                        pages=explicit_pages,
                    )
                )

        # ---------------------------------------------------------
        # 7. Retrieval
        # ---------------------------------------------------------

        results = []

        if "GLOBAL" in retrieval_scopes:

            results.extend(
                await self.retrieval_service.search_global(
                    question=question,
                    query_embedding=query_embedding,
                    chunks=filtered_chunks,
                    top_k=retrieval_top_k,
                    owner_id=owner_id,
                    document_ids=document_ids,
                )
            )

        if "PER_DOCUMENT" in retrieval_scopes:

            results.extend(
                await self.retrieval_service.search_per_document(
                    question=question,
                    query_embedding=query_embedding,
                    chunks=filtered_chunks,
                    top_k=retrieval_top_k,
                    owner_id=owner_id,
                )
            )

        # ---------------------------------------------------------
        # 8. Remove duplicates
        # ---------------------------------------------------------

        results = (
            self.retrieval_service.remove_duplicate_results(
                results
            )
        )

        # ---------------------------------------------------------
        # 9. Preserve explicitly requested pages
        # ---------------------------------------------------------

        if is_page_specific:

            results = (
                self.retrieval_service
                .include_page_chunks(
                    results=results,
                    chunks=chunks,
                    document_ids=document_ids,
                    pages=explicit_pages,
                )
            )

        # ---------------------------------------------------------
        # 10. Sort results
        # ---------------------------------------------------------

        results = self.retrieval_service.sort_results(results)

        # ---------------------------------------------------------
        # 11. Final relevance selection
        # ---------------------------------------------------------

        results = (
            self.retrieval_service.select_relevant_chunks(
                results=results,
                is_broad_question=is_broad_question,
            )
        )

        return {
            "results": results,
            "chunks": chunks,
            "documents": documents,
            "metadata_context": metadata_context,
            "metadata_sources": metadata_sources,
            "retrieval_scopes": retrieval_scopes,
            "explicit_pages": explicit_pages,
            "is_broad_question": is_broad_question,
            "requires_images": query_analysis.requires_visual,
            "is_page_specific": is_page_specific,
        }

    async def search(
        self,
        owner_id: str,
        session_id: str,
        document_ids: list[str],
        question: str,
        history: list | None = None,
        summary: str | None = None,
        top_k: int = 5,
        detail_level: str = "standard",
    ) -> dict:

        try:
            timer = PerformanceLogger()

            # Load user memories (cross-session memory summaries)
            from app.common.constants import CollectionName
            memories_col = self.db[CollectionName.USER_MEMORIES.value]
            memories_doc = await memories_col.find_one({"owner_id": owner_id})
            memories = memories_doc.get("memories", []) if memories_doc else []

            # ============================================================
            # 1. Query Analysis
            # ============================================================

            query_analysis = self.query_analyzer.analyze(question)

            intent_str = str(query_analysis.intent).lower()

            logger.info(
                "Query analysis: intent=%s scope=%s broad=%s visual=%s pages=%s",
                query_analysis.intent,
                query_analysis.scope,
                query_analysis.is_broad,
                query_analysis.requires_visual,
                query_analysis.page_numbers,
            )

            # ============================================================
            # 2. Multi-document structured extraction (for invoices)
            # ============================================================

            invoice_keywords = {
                "invoice", "bill", "billing", "gst", "tax", "subtotal", 
                "grand total", "supplier", "buyer", "vendor", "rate", 
                "amount", "price", "payment", "bank details", "cgst", "sgst"
            }
            q_lower = question.lower()
            is_invoice_comparison = (
                len(document_ids) > 1
                and intent_str == "comparison"
                and any(k in q_lower for k in invoice_keywords)
            )

            if is_invoice_comparison:
                logger.info(
                    "Multi-document invoice comparison request. "
                    "Redirecting to Isolation Extraction Pipeline."
                )

                (
                    md_table,
                    metadata_sources,
                    content_sources,
                ) = await self._run_extraction_pipeline(
                    document_ids=document_ids,
                    question=question,
                    owner_id=owner_id,
                )

                all_sources = {
                    "metadata": metadata_sources,
                    "content": content_sources,
                }

                context = (
                    "=== CONSOLIDATED DOCUMENT RECORDS ===\n\n"
                    f"{md_table}\n\n"
                )

                prompt = self.prompt_builder.build(
                    history=history or [],
                    summary=summary,
                    context=context,
                    question=question,
                    intent=query_analysis.intent,
                    doc_types=["invoice"],
                    detail_level=detail_level,
                    memories=memories,
                )

                response = await self.ai_service.answer_question(
                    prompt=prompt,
                )

                answer = response["answer"]

                answer = self.citation_validator.validate(
                    answer=answer,
                    sources=content_sources,
                )

                return {
                    "answer": answer,
                    "sources": all_sources,
                }

            # ============================================================
            # 3. Shared Retrieval Pipeline
            # ============================================================

            timer.start("Retrieval")

            retrieval_data = await self._retrieve_context(
                question=question,
                document_ids=document_ids,
                owner_id=owner_id,
                query_analysis=query_analysis,
            )

            timer.stop("Retrieval")

            results = retrieval_data["results"]
            chunks = retrieval_data["chunks"]
            documents = retrieval_data["documents"]
            metadata_context = retrieval_data["metadata_context"]
            metadata_sources = retrieval_data["metadata_sources"]
            retrieval_scopes = retrieval_data["retrieval_scopes"]
            explicit_pages = retrieval_data["explicit_pages"]
            is_broad_question = retrieval_data["is_broad_question"]
            requires_images = retrieval_data["requires_images"]

            vision_results = []

            # ============================================================
            # 4. Vision Retrieval
            # ============================================================

            if requires_images:

                image_records = await self._retrieve_images(
                    document_ids=document_ids,
                    results=results,
                    explicit_pages=explicit_pages,
                    requires_images=requires_images,
                )

                vision_results = await self._run_vision(
                    images=image_records,
                    question=question,
                )

            # ============================================================
            # 5. Multi-document synthesis handling
            # ============================================================

            if (
                intent_str in (
                    "summary",
                    "comparison",
                    "general",
                )
                and len(document_ids) > 1
            ):
                logger.info(
                    "Multi-document synthesis triggered for %d documents "
                    "(Intent: %s).",
                    len(document_ids),
                    intent_str,
                )

                results = (
                    self.retrieval_service
                    .ensure_multi_document_coverage(
                        results=results,
                        chunks=chunks,
                        document_ids=document_ids,
                        chunks_per_document=3,
                    )
                )

            # ============================================================
            # 6. TOC handling
            # ============================================================

            if intent_str == "toc" and results:

                logger.info(
                    "TOC intent matched. "
                    "Retrieving sequential TOC pages."
                )

                results = self.retrieval_service.retrieve_toc_chunks(
                    results=results,
                    chunks=chunks,
                )
            # ============================================================
            # 7. Context Compression
            # ============================================================
            original_max_chars = (
                self.token_budget_service.max_characters
            )

            if results:

                timer.start("Context Compressor")

                results = (
                    self.context_compressor_service
                    .compress(results)
                )

                timer.stop("Context Compressor")

                # ========================================================
                # 8. Token Budget
                # ========================================================

                timer.start("Token Budget")

                protected_pages = {
                    (
                        document_id,
                        page_number,
                    )
                    for document_id in document_ids
                    for page_number in explicit_pages
                }

                results = self.token_budget_service.apply(
                    results,
                    ensure_document_coverage=(
                        "PER_DOCUMENT"
                        in retrieval_scopes
                    ),
                    protected_pages=protected_pages,
                )

                self.token_budget_service.max_characters = (
                    original_max_chars
                )

                timer.stop("Token Budget")

                for source_id, result in enumerate(
                    results,
                    start=1,
                ):
                    result["source_id"] = source_id

            else:
                # Always restore the original budget.
                self.token_budget_service.max_characters = (
                    original_max_chars
                )

            # ============================================================
            # 9. No relevant information
            # ============================================================

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

            # ============================================================
            # 10. Build Context
            # ============================================================

            context = self._build_context(
                results=results,
                metadata_context=metadata_context,
                vision_results=vision_results,
                documents=documents,
            )

            # ============================================================
            # 11. Determine Document Types
            # ============================================================

            doc_types = set()

            for document in documents:

                name_lower = (
                    document
                    .get("document_name", "")
                    .lower()
                )

                if any(
                    keyword in name_lower
                    for keyword in (
                        "invoice",
                        "tax_invoice",
                        "receipt",
                        "bill_of_supply",
                    )
                ):
                    doc_types.add("invoice")
                elif any(
                    keyword in name_lower
                    for keyword in (
                        "ppt",
                        "presentation",
                        "slide",
                        "deck",
                        "campaign",
                    )
                ):
                    doc_types.add("presentation")
                elif any(
                    keyword in name_lower
                    for keyword in (
                        "roadmap",
                        "syllabus",
                        "curriculum",
                        "guide",
                        "tutorial",
                        "learning",
                    )
                ):
                    doc_types.add("guide")
                elif any(
                    keyword in name_lower
                    for keyword in (
                        "resume",
                        "cv",
                        "profile",
                        "biodata",
                    )
                ):
                    doc_types.add("resume")
                elif any(
                    keyword in name_lower
                    for keyword in (
                        "contract",
                        "agreement",
                        "nda",
                        "terms",
                    )
                ):
                    doc_types.add("contract")

            question_lower = question.lower()

            if any(
                keyword in question_lower
                for keyword in (
                    "invoice",
                    "tax invoice",
                    "gstin",
                    "subtotal",
                    "grand total",
                    "bill amount",
                )
            ):
                doc_types.add("invoice")

            # ============================================================
            # 12. Prompt
            # ============================================================

            timer.start("Prompt Build")

            prompt = self.prompt_builder.build(
                history=history or [],
                summary=summary,
                context=context,
                question=question,
                intent=query_analysis.intent,
                doc_types=list(doc_types),
                detail_level=detail_level,
                memories=memories,
            )

            timer.stop("Prompt Build")

            # ============================================================
            # 13. LLM
            # ============================================================

            timer.start("LLM")

            response = await self.ai_service.answer_question(
                prompt=prompt,
            )

            answer = response["answer"]

            timer.stop("LLM")

            # ============================================================
            # 14. Usage Logging
            # ============================================================

            await self.ai_usage.log(
                user_id=owner_id,
                session_id=session_id,
                document_id=(
                    document_ids[0]
                    if len(document_ids) == 1
                    else None
                ),
                endpoint="chat",
                prompt_tokens=response["prompt_tokens"],
                completion_tokens=response["completion_tokens"],
                latency_ms=response["latency_ms"],
            )

            # ============================================================
            # 15. Content Sources
            # ============================================================

            content_sources = [
                {
                    "id": result["source_id"],
                    "document_name": (
                        getattr(
                            result["chunk"],
                            "document_name",
                            None,
                        )
                        or next(
                            (
                                document["document_name"]
                                for document in documents
                                if (
                                    document["document_id"]
                                    == result["chunk"].document_id
                                )
                            ),
                            "Unknown Document",
                        )
                    ),
                    "page_number": (
                        result["chunk"].page_number
                    ),
                    "chunk_index": (
                        result["chunk"].chunk_index
                    ),
                    "score": round(
                        result["score"],
                        4,
                    ),
                    "snippet": (
                        result["chunk"].text[:200]
                        + "..."
                        if len(result["chunk"].text) > 200
                        else result["chunk"].text
                    ),
                    "source_type": "content",
                }
                for result in results
            ]

            # ============================================================
            # 16. Vision Sources
            # ============================================================

            for vision in vision_results:

                if not vision.get("result"):
                    continue

                content_sources.append(
                    {
                        "id": vision["source_id"],
                        "document_name": vision["document_id"],
                        "page_number": vision["page_number"],
                        "chunk_index": None,
                        "score": None,
                        "snippet": (
                            vision["result"][:200]
                            + "..."
                            if len(vision["result"]) > 200
                            else vision["result"]
                        ),
                        "source_type": "vision",
                    }
                )

            # ============================================================
            # 17. Citation Validation
            # ============================================================

            answer = self.citation_validator.validate(
                answer=answer,
                sources=content_sources,
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
        detail_level: str = "standard",
    ):
        try:
            # Load user memories (cross-session memory summaries)
            from app.common.constants import CollectionName
            memories_col = self.db[CollectionName.USER_MEMORIES.value]
            memories_doc = await memories_col.find_one({"owner_id": owner_id})
            memories = memories_doc.get("memories", []) if memories_doc else []

            # ============================================================
            # 1. Query Analysis
            # ============================================================

            query_analysis = self.query_analyzer.analyze(
                question
            )

            intent_str = str(
                query_analysis.intent
            ).lower()

            logger.info(
                "Streaming query analysis: intent=%s scope=%s "
                "broad=%s visual=%s pages=%s",
                query_analysis.intent,
                query_analysis.scope,
                query_analysis.is_broad,
                query_analysis.requires_visual,
                query_analysis.page_numbers,
            )

            # ============================================================
            # 2. Multi-document structured extraction (for invoices)
            # ============================================================

            invoice_keywords = {
                "invoice", "bill", "billing", "gst", "tax", "subtotal", 
                "grand total", "supplier", "buyer", "vendor", "rate", 
                "amount", "price", "payment", "bank details", "cgst", "sgst"
            }
            q_lower = question.lower()
            is_invoice_comparison = (
                len(document_ids) > 1
                and intent_str == "comparison"
                and any(k in q_lower for k in invoice_keywords)
            )

            if is_invoice_comparison:

                logger.info(
                    "Multi-document streaming invoice request. "
                    "Using Isolation Extraction Pipeline."
                )

                (
                    md_table,
                    metadata_sources,
                    content_sources,
                ) = await self._run_extraction_pipeline(
                    document_ids=document_ids,
                    question=question,
                    owner_id=owner_id,
                )

                all_sources = {
                    "metadata": metadata_sources,
                    "content": content_sources,
                }

                # Send sources first.
                yield {
                    "type": "sources",
                    "content": all_sources,
                }

                context = (
                    "=== CONSOLIDATED DOCUMENT RECORDS ===\n\n"
                    f"{md_table}\n\n"
                )

                prompt = self.prompt_builder.build(
                    history=history or [],
                    summary=summary,
                    context=context,
                    question=question,
                    intent=query_analysis.intent,
                    doc_types=["invoice"],
                    detail_level=detail_level,
                    memories=memories,
                )

                full_answer = ""

                async for chunk in (
                    self.ai_service.answer_question_stream(
                        prompt=prompt
                    )
                ):

                    full_answer += chunk

                    yield {
                        "type": "chunk",
                        "content": chunk,
                    }

                full_answer = (
                    self.citation_validator.validate(
                        answer=full_answer,
                        sources=content_sources,
                    )
                )

                yield {
                    "type": "done",
                    "content": full_answer,
                }

                return

            # ============================================================
            # 3. Shared Retrieval Pipeline
            # ============================================================

            retrieval_data = await self._retrieve_context(
                question=question,
                document_ids=document_ids,
                owner_id=owner_id,
                query_analysis=query_analysis,
            )

            results = retrieval_data["results"]
            chunks = retrieval_data["chunks"]
            documents = retrieval_data["documents"]
            metadata_context = retrieval_data["metadata_context"]
            metadata_sources = retrieval_data["metadata_sources"]
            retrieval_scopes = retrieval_data["retrieval_scopes"]
            explicit_pages = retrieval_data["explicit_pages"]
            is_broad_question = retrieval_data["is_broad_question"]
            requires_images = retrieval_data["requires_images"]

            # ============================================================
            # 4. Vision
            # ============================================================

            vision_results = []

            if requires_images:

                image_records = await self._retrieve_images(
                    document_ids=document_ids,
                    results=results,
                    explicit_pages=explicit_pages,
                    requires_images=requires_images,
                )

                vision_results = await self._run_vision(
                    images=image_records,
                    question=question,
                )

            # ============================================================
            # 5. Token Budget
            # ============================================================

            original_max_chars = (
                self.token_budget_service.max_characters
            )

            if intent_str in (
                "toc",
                "summary",
                "comparison",
                "general",
            ):
                self.token_budget_service.max_characters = 5000

            try:

                protected_pages = {
                    (
                        document_id,
                        page_number,
                    )
                    for document_id in document_ids
                    for page_number in explicit_pages
                }

                results = self.token_budget_service.apply(
                    results,
                    ensure_document_coverage=(
                        "PER_DOCUMENT"
                        in retrieval_scopes
                    ),
                    protected_pages=protected_pages,
                )

            finally:

                self.token_budget_service.max_characters = (
                    original_max_chars
                )

            # ============================================================
            # 6. Assign Source IDs
            # ============================================================

            for source_id, result in enumerate(
                results,
                start=1,
            ):
                result["source_id"] = source_id

            # ============================================================
            # 7. Build Context
            # ============================================================

            context = self._build_context(
                results=results,
                metadata_context=metadata_context,
                vision_results=vision_results,
                documents=documents,
            )

            # ============================================================
            # 8. Determine Document Types
            # ============================================================

            doc_types = set()

            for document in documents:

                name_lower = (
                    document
                    .get("document_name", "")
                    .lower()
                )

                if any(
                    keyword in name_lower
                    for keyword in (
                        "invoice",
                        "tax_invoice",
                        "receipt",
                        "bill_of_supply",
                    )
                ):
                    doc_types.add("invoice")
                elif any(
                    keyword in name_lower
                    for keyword in (
                        "ppt",
                        "presentation",
                        "slide",
                        "deck",
                        "campaign",
                    )
                ):
                    doc_types.add("presentation")
                elif any(
                    keyword in name_lower
                    for keyword in (
                        "roadmap",
                        "syllabus",
                        "curriculum",
                        "guide",
                        "tutorial",
                        "learning",
                    )
                ):
                    doc_types.add("guide")
                elif any(
                    keyword in name_lower
                    for keyword in (
                        "resume",
                        "cv",
                        "profile",
                        "biodata",
                    )
                ):
                    doc_types.add("resume")
                elif any(
                    keyword in name_lower
                    for keyword in (
                        "contract",
                        "agreement",
                        "nda",
                        "terms",
                    )
                ):
                    doc_types.add("contract")

            if any(
                keyword in question.lower()
                for keyword in (
                    "invoice",
                    "tax invoice",
                    "gstin",
                    "subtotal",
                    "grand total",
                    "bill amount",
                )
            ):
                doc_types.add("invoice")

            # ============================================================
            # 9. Prompt
            # ============================================================

            prompt = self.prompt_builder.build(
                history=history or [],
                summary=summary,
                context=context,
                question=question,
                intent=query_analysis.intent,
                doc_types=list(doc_types),
                detail_level=detail_level,
                memories=memories,
            )

            # ============================================================
            # 10. Content Sources
            # ============================================================

            content_sources = [
                {
                    "id": result["source_id"],
                    "document_name": (
                        getattr(
                            result["chunk"],
                            "document_name",
                            None,
                        )
                        or next(
                            (
                                document["document_name"]
                                for document in documents
                                if (
                                    document["document_id"]
                                    == result["chunk"].document_id
                                )
                            ),
                            "Unknown Document",
                        )
                    ),
                    "page_number": (
                        result["chunk"].page_number
                    ),
                    "chunk_index": (
                        result["chunk"].chunk_index
                    ),
                    "score": round(
                        result["score"],
                        4,
                    ),
                    "snippet": (
                        result["chunk"].text[:200]
                        + "..."
                        if len(result["chunk"].text) > 200
                        else result["chunk"].text
                    ),
                    "source_type": "content",
                }
                for result in results
            ]

            # ============================================================
            # 11. Vision Sources
            # ============================================================

            for vision in vision_results:

                if not vision.get("result"):
                    continue

                content_sources.append(
                    {
                        "id": vision["source_id"],
                        "document_name": vision["document_id"],
                        "page_number": vision["page_number"],
                        "chunk_index": None,
                        "score": None,
                        "snippet": (
                            vision["result"][:200]
                            + "..."
                            if len(vision["result"]) > 200
                            else vision["result"]
                        ),
                        "source_type": "vision",
                    }
                )

            all_sources = {
                "metadata": metadata_sources,
                "content": content_sources,
            }

            # ============================================================
            # 12. Send Sources
            # ============================================================

            yield {
                "type": "sources",
                "content": all_sources,
            }

            # ============================================================
            # 13. Stream LLM Response
            # ============================================================

            full_answer = ""

            async for chunk in (
                self.ai_service.answer_question_stream(
                    prompt=prompt
                )
            ):

                full_answer += chunk

                yield {
                    "type": "chunk",
                    "content": chunk,
                }

            # ============================================================
            # 14. Validate Citations
            # ============================================================

            full_answer = (
                self.citation_validator.validate(
                    answer=full_answer,
                    sources=content_sources,
                )
            )

            # ============================================================
            # 15. Done
            # ============================================================

            yield {
                "type": "done",
                "content": full_answer,
            }

        except SearchException:
            raise

        except BaseAppException:
            raise

        except Exception as exception:

            logger.exception(
                "Document search stream failed."
            )

            raise SearchException(
                str(exception)
            ) from exception