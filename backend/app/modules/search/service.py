import asyncio
import json
import re
from collections import defaultdict

from app.modules.document_chunks.service import (
    DocumentChunkService,
)

from app.services.embedding.gemini import (
    GeminiEmbedding,
)

from app.services.bm25_search.service import (
    BM25SearchService,
)

from app.services.prompt_builder.service import (
    PromptBuilder,
)

from app.services.vision.service import (
    VisionService,
)

from app.services.vector_search.service import (
    VectorSearchService,
)

from app.services.hybrid_search.service import (
    HybridSearchService,
)

from app.services.metadata_filter.service import (
    MetadataFilterService,
)

from app.services.context_compressor.service import (
    ContextCompressor,
)

from app.services.token_budget.service import (
    TokenBudgetService,
)

from app.services.performance_logger.service import (
    PerformanceLogger,
)

from app.common.exceptions.search import (
    SearchException,
)

from app.common.exceptions.auth import (
    BaseAppException,
)

from app.services.cache.embedding_cache import (
    EmbeddingCache,
)

from app.services.ai.service import (
    AIService,
)

from app.services.analytics.ai_usage import (
    AIUsageService,
)

from app.modules.documents.repository import (
    DocumentRepository,
)

from app.services.citation_validator.service import (
    CitationValidator,
)

from app.modules.document_images.service import (
    DocumentImageService,
)

from app.services.image_query.service import (
    ImageQueryService,
)

from app.services.page_query.service import (
    PageQueryService,
)


class SearchService:

    # ------------------------------------------------------------
    # Retrieval configuration
    # ------------------------------------------------------------

    BROAD_QUERY_TERMS = (
        "important",
        "overview",
        "summary",
        "key points",
        "main points",
        "explain",
        "describe",
        "details",
    )

    BROAD_RETRIEVAL_TOP_K = 50

    # Broad questions need page/document diversity rather than
    # simply taking the highest-scoring chunks.
    BROAD_FINAL_CANDIDATE_PAGES = 10
    BROAD_MAX_CHUNKS_PER_PAGE = 2

    # Broad questions should not automatically trigger Vision.
    # Explicit image/page questions and normal visual questions
    # still use the existing Vision path.
    MAX_BROAD_VISUAL_IMAGES = 0

    FRONT_MATTER_TERMS = {
        "declaration",
        "candidate’s declaration",
        "candidate's declaration",
        "certificate",
        "acknowledgement",
        "acknowledgment",
        "table of contents",
        "contents",
        "list of figures",
        "list of tables",
        "abbreviations",
        "training taken at industry",
    }

    # A chunk containing these headings is usually a navigation/administrative
    # chunk rather than the actual body section. We use this as a ranking
    # signal, not an absolute exclusion.
    TOC_SIGNALS = (
        "................................",
        "........................................",
        "................................................................",
        "table of contents",
    )

    SECTION_SIGNALS = (
        "introduction",
        "purpose",
        "scope",
        "objective",
        "technology",
        "literature review",
        "project management",
        "feasibility study",
        "system requirements",
        "functional requirements",
        "non functional requirements",
        "system design",
        "architecture",
        "implementation",
        "testing",
        "results",
        "conclusion",
    )

    STOP_WORDS = {
        "give",
        "me",
        "the",
        "a",
        "an",
        "is",
        "are",
        "what",
        "which",
        "show",
        "tell",
        "about",
        "from",
        "of",
        "in",
        "on",
        "for",
        "to",
        "with",
        "important",
        "things",
        "details",
        "information",
    }

    def __init__(self, db):

        self.chunk_service = DocumentChunkService(db)

        self.document_repository = (
            DocumentRepository(db)
        )

        self.embedding_service = GeminiEmbedding()

        self.vector_service = VectorSearchService()

        self.bm25_service = BM25SearchService()

        self.prompt_builder = PromptBuilder()

        self.context_compressor_service = (
            ContextCompressor()
        )

        self.token_budget_service = (
            TokenBudgetService()
        )

        self.hybrid_search_service = (
            HybridSearchService()
        )

        self.metadata_filter_service = (
            MetadataFilterService()
        )

        self.ai_service = AIService()

        self.document_image_service = (
            DocumentImageService(db)
        )

        self.vision_service = VisionService(
            ai_service=self.ai_service,
            document_image_service=(
                self.document_image_service
            ),
        )

        self.embedding_cache = EmbeddingCache()

        self.ai_usage = AIUsageService(db)

        self.citation_validator = (
            CitationValidator()
        )

        self.image_query_service = (
            ImageQueryService()
        )

        self.page_query_service = (
            PageQueryService()
        )

    # ============================================================
    # QUERY HELPERS
    # ============================================================

    def _is_broad_question(
        self,
        question: str,
    ) -> bool:

        normalized = question.lower()

        return any(
            term in normalized
            for term in self.BROAD_QUERY_TERMS
        )

    def _extract_question_terms(
        self,
        question: str,
    ) -> list[str]:

        normalized = question.lower()

        return [
            word
            for word in re.findall(
                r"\b[a-zA-Z0-9_]+\b",
                normalized,
            )
            if word not in self.STOP_WORDS
        ]

    def _structure_score(self, text: str) -> float:
        """
        Estimate whether a chunk looks like actual document body content.

        This is intentionally heuristic and document-agnostic. It does not
        assume particular page numbers or a particular report format.
        """

        normalized = re.sub(
            r"\\s+",
            " ",
            text.lower(),
        ).strip()

        if not normalized:
            return 0.0

        score = 0.0

        # Strong signal that this is a TOC/navigation line.
        toc_signal_count = sum(
            normalized.count(signal)
            for signal in self.TOC_SIGNALS
        )

        if toc_signal_count:
            score -= min(
                0.60,
                0.20 * toc_signal_count,
            )

        # Administrative/front matter.
        front_matter_count = sum(
            1
            for term in self.FRONT_MATTER_TERMS
            if term in normalized
        )

        if front_matter_count:
            score -= min(
                0.45,
                0.15 * front_matter_count,
            )

        # Real section/body signals.
        section_count = sum(
            1
            for term in self.SECTION_SIGNALS
            if re.search(
                rf"\\b{re.escape(term)}\\b",
                normalized,
            )
        )

        score += min(
            0.35,
            0.08 * section_count,
        )

        # Body text generally contains more than a short list of headings.
        word_count = len(
            re.findall(
                r"\\b[a-zA-Z0-9][a-zA-Z0-9_-]*\\b",
                normalized,
            )
        )

        if word_count >= 80:
            score += 0.10
        elif word_count >= 40:
            score += 0.05

        return max(-1.0, min(score, 1.0))

    def _is_toc_like(self, text: str) -> bool:
        normalized = re.sub(
            r"\\s+",
            " ",
            text.lower(),
        ).strip()

        if not normalized:
            return False

        # Dotted leader lines are a strong TOC indicator.
        dotted_leaders = bool(
            re.search(
                r"\\.{4,}",
                normalized,
            )
        )

        heading_count = sum(
            1
            for term in self.SECTION_SIGNALS
            if re.search(
                rf"\\b{re.escape(term)}\\b",
                normalized,
            )
        )

        # A chunk with many section headings and dotted leaders is almost
        # certainly navigation rather than body content.
        return (
            dotted_leaders
            and heading_count >= 2
        ) or (
            "table of contents" in normalized
        )

    def _adjust_broad_results(
        self,
        results: list[dict],
        question: str,
    ) -> list[dict]:

        """
        Improve broad-query ranking without hard-coding document pages.

        Important distinction:
        - semantic/vector relevance tells us what the question resembles
        - structure signals tell us whether the chunk is actual content
          or merely a TOC/front-matter reference

        The second signal is deliberately weaker than retrieval relevance.
        """

        question_terms = (
            self._extract_question_terms(question)
        )

        for result in results:

            text = (
                result["chunk"]
                .text
                .lower()
            )

            # --------------------------------------------------------
            # Query-term relevance
            # --------------------------------------------------------

            lexical_score = 0.0

            if question_terms:

                matched_terms = sum(
                    1
                    for term in question_terms
                    if re.search(
                        rf"\\b{re.escape(term)}\\b",
                        text,
                    )
                )

                lexical_score = (
                    matched_terms
                    / len(question_terms)
                )

            # Keep this modest. Hybrid retrieval is still the primary
            # relevance signal.
            result["score"] += (
                lexical_score * 0.15
            )

            # --------------------------------------------------------
            # Document structure
            # --------------------------------------------------------

            structure_score = (
                self._structure_score(text)
            )

            result["score"] += (
                structure_score * 0.35
            )

            # Stronger penalty for a TOC-like chunk.
            if self._is_toc_like(text):

                result["score"] *= 0.55

            # Administrative pages should lose when they don't contain
            # an actual requested concept.
            has_front_matter = any(
                term in text
                for term in self.FRONT_MATTER_TERMS
            )

            contains_requested_term = any(
                re.search(
                    rf"\\b{re.escape(term)}\\b",
                    text,
                )
                for term in question_terms
            )

            if (
                has_front_matter
                and not contains_requested_term
            ):
                result["score"] *= 0.70

        return sorted(
            results,
            key=lambda item: item["score"],
            reverse=True,
        )

    def _select_broad_text_results(
        self,
        results: list[dict],
    ) -> list[dict]:

        """
        Select representative content for broad questions.

        Normal retrieval answers:
            "What does the document say about JWT?"

        Broad retrieval answers:
            "What are the important things in this document?"

        For broad questions, the highest-scoring chunks often cluster
        around the cover page, acknowledgement, certificate, and TOC.
        This selector therefore works at PAGE level and rewards:

        - strong retrieval score
        - different pages
        - different documents
        - multiple useful chunks from a page

        It does NOT hard-code page numbers or document-specific rules.
        """

        if not results:
            return []

        # ------------------------------------------------------------
        # Group retrieved chunks by document + page
        # ------------------------------------------------------------

        page_groups: dict[
            tuple[str, int],
            list[dict],
        ] = defaultdict(list)

        for result in results:

            chunk = result["chunk"]

            key = (
                chunk.document_id,
                chunk.page_number,
            )

            page_groups[key].append(result)

        # ------------------------------------------------------------
        # Score each page
        # ------------------------------------------------------------

        page_candidates = []

        for (
            document_page,
            page_results,
        ) in page_groups.items():

            page_results = sorted(
                page_results,
                key=lambda item: item["score"],
                reverse=True,
            )

            best_score = float(
                page_results[0].get(
                    "score",
                    0.0,
                )
            )

            # A second chunk on the same page is useful,
            # but should not dominate page diversity.
            supporting_score = 0.0

            if len(page_results) > 1:
                supporting_score = (
                    float(
                        page_results[1].get(
                            "score",
                            0.0,
                        )
                    )
                    * 0.20
                )

            page_score = (
                best_score
                + supporting_score
            )

            text = " ".join(
                result["chunk"].text.lower()
                for result in page_results[:3]
            )

            # Generic front-matter penalty.
            # It is only a penalty, never an exclusion.
            page_structure = (
                self._structure_score(text)
            )

            page_score += (
                page_structure * 0.25
            )

            if self._is_toc_like(text):
                page_score *= 0.55
            elif any(
                term in text
                for term in self.FRONT_MATTER_TERMS
            ):
                page_score *= 0.70

            page_candidates.append(
                {
                    "key": document_page,
                    "score": page_score,
                    "results": page_results,
                }
            )

        # ------------------------------------------------------------
        # Greedy diversity selection
        # ------------------------------------------------------------

        page_candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        selected_pages = []
        selected_documents = defaultdict(int)

        while (
            page_candidates
            and len(selected_pages)
            < self.BROAD_FINAL_CANDIDATE_PAGES
        ):

            best_candidate = None
            best_value = float("-inf")

            for candidate in page_candidates:

                document_id, page_number = (
                    candidate["key"]
                )

                # Avoid repeatedly selecting the same document/page.
                if any(
                    selected["key"]
                    == candidate["key"]
                    for selected in selected_pages
                ):
                    continue

                value = candidate["score"]

                # Mild diversity bonus. This helps multi-document
                # broad questions without hurting single-document
                # retrieval.
                if selected_documents[
                    document_id
                ] == 0:
                    value += 0.05

                # Mild page-distance bonus prevents a broad result
                # from becoming a cluster of adjacent front-matter pages.
                if selected_pages:

                    selected_page_numbers = [
                        selected["key"][1]
                        for selected in selected_pages
                        if selected["key"][0]
                        == document_id
                    ]

                    if selected_page_numbers:

                        min_distance = min(
                            abs(
                                page_number - page
                            )
                            for page
                            in selected_page_numbers
                        )

                        if min_distance >= 3:
                            value += 0.04
                        elif min_distance == 0:
                            value -= 0.10

                if value > best_value:

                    best_value = value
                    best_candidate = candidate

            if best_candidate is None:
                break

            selected_pages.append(
                best_candidate
            )

            selected_documents[
                best_candidate["key"][0]
            ] += 1

            page_candidates.remove(
                best_candidate
            )

        # ------------------------------------------------------------
        # Flatten selected pages into chunks
        # ------------------------------------------------------------

        selected_results = []

        for page in selected_pages:

            page_results = sorted(
                page["results"],
                key=lambda item: item["score"],
                reverse=True,
            )

            selected_results.extend(
                page_results[
                    :self.BROAD_MAX_CHUNKS_PER_PAGE
                ]
            )

        # Keep strongest chunks first for downstream compression/token
        # budgeting, while preserving the page diversity already selected.
        selected_results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        print(
            "\n========== BROAD TEXT SELECTION =========="
        )

        for rank, result in enumerate(
            selected_results,
            start=1,
        ):

            chunk = result["chunk"]

            print(
                f"{rank}. "
                f"page={chunk.page_number} | "
                f"chunk={chunk.chunk_index} | "
                f"score={result['score']:.4f}"
            )

        print(
            "Selected pages:",
            [
                (
                    page["key"][0],
                    page["key"][1],
                )
                for page in selected_pages
            ],
        )

        print(
            "Selected chunks:",
            len(selected_results),
        )

        print(
            "==========================================\n"
        )

        return selected_results

    # ============================================================
    # BROAD VISUAL PAGE SELECTION
    # ============================================================

    def _select_broad_visual_pages(
        self,
        all_image_pages: set[tuple[str, int]],
        retrieval_results: list[dict],
    ) -> dict[str, list[int]]:

        image_page_set = set(all_image_pages)

        page_scores = defaultdict(list)

        for result in retrieval_results:

            chunk = result["chunk"]

            key = (
                chunk.document_id,
                chunk.page_number,
            )

            if key not in image_page_set:
                continue

            score = float(
                result.get("score", 0.0)
            )

            page_scores[key].append(score)

        ranked_pages = []

        for key, scores in page_scores.items():

            scores.sort(reverse=True)

            # Strongest chunk gets most importance.
            # Additional chunks provide supporting evidence.
            page_score = scores[0]

            if len(scores) > 1:
                page_score += scores[1] * 0.30

            if len(scores) > 2:
                page_score += scores[2] * 0.15

            ranked_pages.append(
                (
                    key,
                    page_score,
                    len(scores),
                )
            )

        ranked_pages.sort(
            key=lambda item: (
                -item[1],
                -item[2],
                item[0][0],
                item[0][1],
            )
        )

        selected = defaultdict(list)

        for (
            (document_id, page_number),
            score,
            chunk_count,
        ) in ranked_pages[
            :self.MAX_BROAD_VISUAL_PAGES
        ]:

            selected[document_id].append(
                page_number
            )

        selected = {
            document_id: sorted(pages)
            for document_id, pages
            in selected.items()
        }

        print(
            "\n========== BROAD VISUAL PAGE RANKING =========="
        )

        for rank, (
            (document_id, page_number),
            score,
            chunk_count,
        ) in enumerate(
            ranked_pages[:10],
            start=1,
        ):

            print(
                f"{rank}. "
                f"page={page_number} | "
                f"score={score:.4f} | "
                f"chunks={chunk_count}"
            )

        print(
            "Selected broad visual pages:",
            selected,
        )

        print(
            "===============================================\n"
        )

        return selected

    # ============================================================
    # RETRIEVAL SCOPES
    # ============================================================

    async def _determine_retrieval_scopes(
        self,
        question: str,
        document_count: int,
    ) -> list[str]:

        if document_count <= 1:
            return ["GLOBAL"]

        prompt = f"""
You are a retrieval planner for an AI document reader.

The user may ask multiple things in one question.

Return ONLY valid JSON:

{{
    "scopes": [
        "METADATA",
        "PER_DOCUMENT",
        "GLOBAL"
    ]
}}

Available scopes:

METADATA:
- number of documents
- file names
- page counts
- file types
- file sizes
- upload status

PER_DOCUMENT:
- key points for every document
- summary of every document
- details of every document
- explain each document

GLOBAL:
- find information
- explain a topic
- compare information
- locate information
- questions about document content

Rules:

1. Return every scope required.
2. Metadata-only questions use only METADATA.
3. Questions about every document use PER_DOCUMENT.
4. General document-content questions use GLOBAL.
5. Multiple scopes are allowed.
6. Do not duplicate scopes.
7. Preserve order:
   METADATA → PER_DOCUMENT → GLOBAL

Question:
{question}
"""

        try:

            response = (
                await self.ai_service
                .answer_question(
                    prompt=prompt
                )
            )

            raw_answer = (
                response["answer"]
                .strip()
            )

            if raw_answer.startswith("```"):

                raw_answer = (
                    raw_answer
                    .replace(
                        "```json",
                        "",
                        1,
                    )
                    .replace(
                        "```",
                        "",
                        1,
                    )
                    .strip()
                )

            result = json.loads(
                raw_answer
            )

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

            if not scopes:
                return ["GLOBAL"]

            return list(
                dict.fromkeys(scopes)
            )

        except Exception:
            return ["GLOBAL"]

    # ============================================================
    # GLOBAL SEARCH
    # ============================================================

    async def _search_global(
        self,
        question: str,
        query_embedding: list[float],
        chunks,
        top_k: int,
    ):

        bm25_results = (
            self.bm25_service.search(
                question=question,
                chunks=chunks,
                top_k=top_k,
            )
        )

        vector_results = (
            self.vector_service.search(
                query_embedding=query_embedding,
                chunks=chunks,
                top_k=top_k,
            )
        )

        return (
            self.hybrid_search_service.merge(
                vector_results=vector_results,
                keyword_results=bm25_results,
                top_k=top_k,
                question=question,
            )
        )

    # ============================================================
    # METADATA
    # ============================================================

    async def _get_document_metadata(
        self,
        document_ids: list[str],
    ):

        documents = []

        for document_id in document_ids:

            document = (
                await self.document_repository
                .get_document_by_id(
                    document_id
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
                    "page_count": (
                        document.page_count
                    ),
                    "file_size": (
                        document.file_size
                    ),
                    "mime_type": (
                        document.mime_type
                    ),
                    "status": (
                        document.status
                    ),
                }
            )

        return documents

    # ============================================================
    # PER DOCUMENT SEARCH
    # ============================================================

    async def _search_per_document(
        self,
        question: str,
        query_embedding: list[float],
        chunks,
        top_k: int,
    ):

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

        for (
            document_id,
            document_chunks,
        ) in grouped_chunks.items():

            print(
                f"Document {document_id}: "
                f"{len(document_chunks)} chunks"
            )

            bm25_results = (
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

            document_results = (
                self.hybrid_search_service.merge(
                    vector_results=vector_results,
                    keyword_results=bm25_results,
                    top_k=top_k,
                    question=question,
                )
            )

            results.extend(
                document_results
            )

        return results

    # ============================================================
    # MAIN SEARCH
    # ============================================================

    async def search(
        self,
        owner_id: str,
        session_id: str,
        document_ids: list[str],
        question: str,
        history: list | None = None,
        summary: str | None = None,
        top_k: int = 5,
    ):

        normalized_question = (
            question.lower()
        )

        # --------------------------------------------------------
        # Detect broad question ONCE
        # --------------------------------------------------------

        is_broad_question = (
            self._is_broad_question(
                question
            )
        )

        requires_images = (
            self.image_query_service
            .requires_images(question)
        )

        explicit_pages = (
            self.page_query_service
            .extract_page_numbers(question)
        )

        print(
            f"Image retrieval required: "
            f"{requires_images}"
        )

        print(
            f"Explicit pages: "
            f"{explicit_pages}"
        )

        print(
            f"Broad question: "
            f"{is_broad_question}"
        )

        try:

            timer = PerformanceLogger()

            # ====================================================
            # RETRIEVAL SCOPE
            # ====================================================

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

            # Broad multi-document questions should
            # represent every document.

            if (
                is_broad_question
                and len(document_ids) > 1
                and "PER_DOCUMENT"
                not in retrieval_scopes
            ):
                retrieval_scopes.append(
                    "PER_DOCUMENT"
                )

            print(
                "Retrieval scopes:",
                retrieval_scopes,
            )

            # ====================================================
            # RETRIEVAL SIZE
            # ====================================================

            retrieval_top_k = (
                self.BROAD_RETRIEVAL_TOP_K
                if is_broad_question
                else top_k
            )

            print(
                "Broad question:",
                is_broad_question,
                "| Retrieval top_k:",
                retrieval_top_k,
                "| Final top_k:",
                top_k,
                "| Final scopes:",
                retrieval_scopes,
            )

            # ====================================================
            # INITIALIZE
            # ====================================================

            metadata_context = ""
            metadata_sources = []

            documents = []

            results = []

            vision_page_results = []

            # ====================================================
            # METADATA
            # ====================================================

            if "METADATA" in retrieval_scopes:

                documents = (
                    await self._get_document_metadata(
                        document_ids
                    )
                )

                metadata_context = "\n".join(
                    [
                        (
                            f"Document: "
                            f"{doc['document_name']}\n"
                            f"Page count: "
                            f"{doc['page_count']}\n"
                            f"File size: "
                            f"{doc['file_size']}\n"
                            f"File type: "
                            f"{doc['mime_type']}\n"
                            f"Status: "
                            f"{doc['status']}\n"
                        )
                        for doc in documents
                    ]
                )

                metadata_sources = [
                    {
                        "id": doc[
                            "document_id"
                        ],
                        "document_name": doc[
                            "document_name"
                        ],
                        "page_count": doc[
                            "page_count"
                        ],
                        "file_size": doc[
                            "file_size"
                        ],
                        "mime_type": doc[
                            "mime_type"
                        ],
                        "status": doc[
                            "status"
                        ],
                        "source_type": "metadata",
                    }
                    for doc in documents
                ]

            # ====================================================
            # CONTENT PREPARATION
            # ====================================================

            query_embedding = None
            chunks = []

            if (
                "GLOBAL"
                in retrieval_scopes
                or "PER_DOCUMENT"
                in retrieval_scopes
            ):

                timer.start(
                    "Embedding"
                )

                query_embedding = (
                    await self.embedding_cache
                    .get(question)
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

                    print(
                        "Embedding created and cached "
                        f"for question: {question}"
                    )

                else:

                    print(
                        "Embedding loaded from Redis "
                        f"for question: {question}"
                    )

                timer.stop(
                    "Embedding"
                )

                chunks = (
                    await self.chunk_service
                    .get_chunks_with_embeddings(
                        document_ids
                    )
                )
                # print(
                #     "\n========== CHUNK DEBUG =========="
                # )

                # print(
                #     "Total chunks loaded:",
                #     len(chunks),
                # )

                # print(
                #     "Chunk pages:",
                #     sorted(
                #         {
                #             (
                #                 chunk.document_id,
                #                 chunk.page_number,
                #             )
                #             for chunk in chunks
                #         }
                #     )
                # )

                # print(
                #     "=================================\n"
                # )
            # ====================================================
            # LOAD IMAGE INFORMATION
            # ====================================================

            all_images = (
                await self.document_image_service
                .get_images_for_documents(
                    document_ids
                )
            )

            all_image_pages = {
                (
                    image["document_id"],
                    image["page_number"],
                )
                for image in all_images
            }

            print(
                "ALL IMAGE PAGES:",
                sorted(
                    {
                        image["page_number"]
                        for image in all_images
                    }
                ),
            )

            # Explicit pages directly enable images
            # when images exist on those pages.

            if explicit_pages:

                requested_image_pages = {
                    (
                        document_id,
                        page,
                    )
                    for document_id in document_ids
                    for page in explicit_pages
                    if (
                        document_id,
                        page,
                    ) in all_image_pages
                }

                if requested_image_pages:

                    requires_images = True

                    print(
                        "Page-specific image retrieval required:",
                        requested_image_pages,
                    )

            # ====================================================
            # GLOBAL RETRIEVAL
            # ====================================================

            if "GLOBAL" in retrieval_scopes:

                timer.start(
                    "Metadata Filter"
                )

                filtered_chunks = (
                    self.metadata_filter_service
                    .filter(
                        question=question,
                        chunks=chunks,
                    )
                )
                # print(
                #     "\n========== FILTER DEBUG =========="
                # )

                # print(
                #     "Chunks before filter:",
                #     len(chunks),
                # )

                # print(
                #     "Chunks after filter:",
                #     len(filtered_chunks),
                # )

                # print(
                #     "Filtered pages:",
                #     sorted(
                #         {
                #             (
                #                 chunk.document_id,
                #                 chunk.page_number,
                #             )
                #             for chunk in filtered_chunks
                #         }
                #     )
                # )

                # print(
                #     "==================================\n"
                # )

                timer.stop(
                    "Metadata Filter"
                )

                timer.start(
                    "Global Retrieval"
                )

                global_results = (
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

                results.extend(
                    global_results
                )

            else:

                filtered_chunks = chunks

            # ====================================================
            # PER DOCUMENT RETRIEVAL
            # ====================================================

            if "PER_DOCUMENT" in retrieval_scopes:

                timer.start(
                    "Per Document Retrieval"
                )

                per_document_results = (
                    await self._search_per_document(
                        question=question,
                        query_embedding=(
                            query_embedding
                        ),
                        chunks=chunks,
                        top_k=retrieval_top_k,
                    )
                )

                timer.stop(
                    "Per Document Retrieval"
                )

                results.extend(
                    per_document_results
                )

            # ====================================================
            # REMOVE DUPLICATES
            # ====================================================

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

                unique_results.append(
                    result
                )

            results = unique_results

            # ====================================================
            # BROAD RESULT ADJUSTMENT
            # ====================================================

            if is_broad_question:

                results = (
                    self._adjust_broad_results(
                        results=results,
                        question=question,
                    )
                )

                # Replace score-only ranking with representative
                # page-level selection for broad questions.
                results = (
                    self._select_broad_text_results(
                        results
                    )
                )

            # ====================================================
            # EXPLICIT PAGE TEXT
            # ====================================================

            if explicit_pages:

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
                        result["chunk"]
                        .document_id,
                        result["chunk"]
                        .page_number,
                        result["chunk"]
                        .chunk_index,
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

            print(
                "Final image retrieval required:",
                requires_images,
            )

            # ====================================================
            # IMAGE RETRIEVAL
            # ====================================================

            image_records = []

            if requires_images:

                # ------------------------------------------------
                # EXPLICIT PAGES
                # ------------------------------------------------

                if explicit_pages:

                    page_results = [
                        result
                        for result in results
                        if (
                            result["chunk"]
                            .document_id
                            in document_ids
                            and result["chunk"]
                            .page_number
                            in explicit_pages
                        )
                    ]

                    if page_results:
                        results = page_results

                    page_numbers = {
                        document_id: explicit_pages
                        for document_id in document_ids
                    }

                    image_records = (
                        await self.document_image_service
                        .get_images_for_query(
                            document_ids=document_ids,
                            page_numbers=page_numbers,
                            limit=10,
                        )
                    )

                # ------------------------------------------------
                # BROAD QUESTION
                # ------------------------------------------------

                elif is_broad_question:

                    # Broad questions do not automatically trigger Vision.
                    # Vision remains available for explicit page/image
                    # requests and normal visual questions.
                    image_records = []

                # ------------------------------------------------
                # NORMAL VISUAL QUESTION
                # ------------------------------------------------

                else:

                    relevant_pages = defaultdict(
                        set
                    )

                    for result in results:

                        chunk = result["chunk"]

                        relevant_pages[
                            chunk.document_id
                        ].add(
                            chunk.page_number
                        )

                    page_numbers = {
                        document_id: list(
                            pages
                        )
                        for (
                            document_id,
                            pages,
                        )
                        in relevant_pages.items()
                    }

                    image_records = (
                        await self.document_image_service
                        .get_images_for_query(
                            document_ids=document_ids,
                            page_numbers=page_numbers,
                            limit=10,
                        )
                    )

                    if not image_records:

                        print(
                            "No images found for relevant pages."
                        )

                        image_records = (
                            await self.document_image_service
                            .get_images_for_query(
                                document_ids=document_ids,
                                limit=10,
                            )
                        )

                # =================================================
                # VISION
                # =================================================

                print(
                    "Image candidates:",
                    len(image_records),
                )

                if image_records:

                    try:

                        vision_page_results = (
                            await self.vision_service
                            .analyze_images_by_page(
                                images=image_records,
                                prompt=question,
                            )
                        )

                    except asyncio.CancelledError:

                        print(
                            "🛑 Vision analysis cancelled."
                        )

                        raise

                    except Exception as exception:

                        print(
                            "Vision analysis failed:",
                            str(exception),
                        )

                        vision_page_results = []

                    print(
                        "========== VISION RESULT =========="
                    )

                    for result in (
                        vision_page_results
                    ):

                        print(
                            "PAGE:",
                            result["page_number"],
                        )

                        print(
                            result["result"]
                        )

                    print(
                        "===================================="
                    )

            # ====================================================
            # FINAL RESULT RANKING
            # ====================================================

            results.sort(
                key=lambda item: item["score"],
                reverse=True,
            )

            # Keep broad retrieval large for discovery,
            # but allow downstream services to reduce it.

            # ====================================================
            # CONTEXT COMPRESSION
            # ====================================================

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

                # ------------------------------------------------
                # TOKEN BUDGET
                # ------------------------------------------------

                timer.start(
                    "Token Budget"
                )

                results = (
                    self.token_budget_service.apply(
                        results,
                        ensure_document_coverage=(
                            "PER_DOCUMENT"
                            in retrieval_scopes
                        ),
                    )
                )

                timer.stop(
                    "Token Budget"
                )

                for source_id, result in enumerate(
                    results,
                    start=1,
                ):

                    result[
                        "source_id"
                    ] = source_id

            # ====================================================
            # NO CONTEXT
            # ====================================================

            if (
                not results
                and not metadata_context
                and not vision_page_results
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

            # ====================================================
            # BUILD CONTEXT
            # ====================================================

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

            # ====================================================
            # VISUAL CONTEXT
            # ====================================================

            vision_source_id = (
                len(results) + 1
            )

            if vision_page_results:

                context += (
                    "=== VISUAL INFORMATION ===\n"
                )

                for result in (
                    vision_page_results
                ):

                    if not result.get(
                        "result"
                    ):
                        continue

                    result[
                        "source_id"
                    ] = vision_source_id

                    context += (
                        f"[SOURCE_{vision_source_id}]\n"
                        f"Document: "
                        f"{result['document_id']}\n"
                        f"Page: "
                        f"{result['page_number']}\n"
                        f"Content:\n"
                        f"{result['result']}\n\n"
                    )

                    vision_source_id += 1

            # ====================================================
            # PROMPT
            # ====================================================

            timer.start(
                "Prompt Build"
            )

            prompt = (
                self.prompt_builder.build(
                    history=history or [],
                    summary=summary,
                    context=context,
                    question=question,
                )
            )

            timer.stop(
                "Prompt Build"
            )

            # ====================================================
            # LLM
            # ====================================================

            timer.start("LLM")

            response = (
                await self.ai_service
                .answer_question(
                    prompt=prompt,
                )
            )

            answer = response["answer"]

            timer.stop("LLM")

            # ====================================================
            # AI USAGE
            # ====================================================

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

            timer.print()

            # ====================================================
            # SOURCES
            # ====================================================

            content_sources = [
                {
                    "id": result[
                        "source_id"
                    ],
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

            for vision in (
                vision_page_results
            ):

                if not vision.get(
                    "result"
                ):
                    continue

                content_sources.append(
                    {
                        "id": vision[
                            "source_id"
                        ],
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

            # ====================================================
            # CITATION VALIDATION
            # ====================================================

            answer = (
                self.citation_validator.validate(
                    answer=answer,
                    sources=content_sources,
                )
            )

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

            raise SearchException(
                str(exception)
            ) from exception