from app.core.config import settings

import json
from collections import defaultdict

from app.modules.document_chunks.service import (
    DocumentChunkService,
)

from app.services.ai.gemini import (
    GeminiAIService,
)
from app.services.ai.groq import (
    GroqAIService,
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
from app.services.vector_search.service import (
    VectorSearchService,
)
from app.services.hybrid_search.service import( HybridSearchService)

from app.services.metadata_filter.service import (  MetadataFilterService)

from app.services.context_compressor.service import (ContextCompressor)

from app.services.token_budget.service import (TokenBudgetService)

from app.services.performance_logger.service import(PerformanceLogger)
from app.common.exceptions.search import (
    SearchException,
)
from app.services.cache.embedding_cache import (
    EmbeddingCache,
)
from app.services.ai.service import AIService
from app.services.analytics.ai_usage import AIUsageService
from app.modules.documents.repository import DocumentRepository

class SearchService:

    def __init__(self, db):

        self.chunk_service = DocumentChunkService(db)

        self.document_repository = DocumentRepository(db)

        self.embedding_service = GeminiEmbedding()

        self.vector_service = VectorSearchService()

        self.bm25_service = BM25SearchService()

        self.prompt_builder = PromptBuilder()

        self.context_compressor_service = ContextCompressor()

        self.token_budget_service = TokenBudgetService()

        self.hybrid_search_service = HybridSearchService()

        self.metadata_filter_service = MetadataFilterService()

        self.ai_service = AIService()

        self.embedding_cache = EmbeddingCache()

        self.ai_usage = AIUsageService(db)



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

    Return ONLY valid JSON in this format:

    {{
        "scopes": [
            "METADATA",
            "PER_DOCUMENT",
            "GLOBAL"
        ]
    }}

    Available scopes:

    METADATA:
    Questions about document metadata:
    - number of documents
    - file names
    - page counts
    - file types
    - file sizes
    - upload status

    PER_DOCUMENT:
    Questions requiring information from EACH document:
    - key points for every document
    - summary of every document
    - details of every document
    - explain each document

    GLOBAL:
    Questions requiring content retrieval from the documents:
    - find information
    - explain a topic
    - compare information
    - locate information
    - questions about specific content

    Rules:

    1. Return every scope required by the question.
    2. If the question asks only for metadata, return only METADATA.
    3. If the question asks for details from every document, include PER_DOCUMENT.
    4. If the question asks about document content generally, include GLOBAL.
    5. Multiple scopes are allowed.
    6. Do not return duplicate scopes.
    7. Preserve the order:
    METADATA → PER_DOCUMENT → GLOBAL

    Examples:

    Question:
    "How many documents are uploaded?"
    Response:
    {{"scopes":["METADATA"]}}

    Question:
    "Give me 3 key points from every document."
    Response:
    {{"scopes":["PER_DOCUMENT"]}}

    Question:
    "Which document contains JWT information?"
    Response:
    {{"scopes":["GLOBAL"]}}

    Question:
    "List all file names and give 3 key points for each."
    Response:
    {{"scopes":["METADATA","PER_DOCUMENT"]}}

    Question:
    "List all files, summarize each one, and tell me which document discusses JWT."
    Response:
    {{"scopes":["METADATA","PER_DOCUMENT","GLOBAL"]}}

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

            scopes = result.get("scopes", [])

            valid_scopes = {
                "METADATA",
                "PER_DOCUMENT",
                "GLOBAL",
            }

            scopes = [
                scope
                for scope in scopes
                if scope in valid_scopes
            ]

            if not scopes:
                return ["GLOBAL"]

            return list(dict.fromkeys(scopes))

        except Exception:

            return ["GLOBAL"]

    async def _search_global(
        self,
        question: str,
        query_embedding: list[float],
        chunks,
        top_k: int,
    ):

        bm25_results = self.bm25_service.search(
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
            keyword_results=bm25_results,
            top_k=top_k,
        )

    async def _get_document_metadata(
        self,
        document_ids: list[str],
    ):
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

        for document_id, document_chunks in grouped_chunks.items():
            print(
                f"Document {document_id}: "
                f"{len(document_chunks)} chunks"
            )

            bm25_results = self.bm25_service.search(
                question=question,
                chunks=document_chunks,
                top_k=candidate_k,
            )

            vector_results = self.vector_service.search(
                query_embedding=query_embedding,
                chunks=document_chunks,
                top_k=candidate_k,
            )

            document_results = (
                self.hybrid_search_service.merge(
                    vector_results=vector_results,
                    keyword_results=bm25_results,
                    top_k=top_k,
                )
            )

            print(
                f"Retrieved {len(document_results)} chunks "
                f"for document {document_id}"
            )            
            results.extend(
                document_results
            )
            print(f"total retrived chunks {len(results)}")

        return results

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
        try:

            timer = PerformanceLogger()

            # -----------------------------
            # Retrieval Scope
            # -----------------------------
            timer.start("Retrieval Scope")

            retrieval_scopes = (
                await self._determine_retrieval_scopes(
                    question=question,
                    document_count=len(document_ids),
                )
            )

            timer.stop("Retrieval Scope")

            print(
                f"Retrieval scopes: {retrieval_scopes}"
            )

            # -----------------------------
            # Metadata
            # -----------------------------
            metadata_context = ""

            if "METADATA" in retrieval_scopes:

                documents = (
                    await self._get_document_metadata(
                        document_ids
                    )
                )

                metadata_context = "\n".join(
                    [
                        (
                            f"Document: {doc['document_name']}\n"
                            f"Page count: {doc['page_count']}\n"
                            f"File size: {doc['file_size']}\n"
                            f"File type: {doc['mime_type']}\n"
                            f"Status: {doc['status']}\n"
                        )
                        for doc in documents
                    ]
                )

            # -----------------------------
            # Content Retrieval Preparation
            # -----------------------------
            query_embedding = None
            chunks = []

            if (
                "GLOBAL" in retrieval_scopes
                or "PER_DOCUMENT" in retrieval_scopes
            ):

                # -----------------------------
                # Embedding
                # -----------------------------
                timer.start("Embedding")

                query_embedding = (
                    await self.embedding_cache.get(
                        question
                    )
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

                    print(
                        "Embedding created and cached "
                        f"for question: {question}"
                    )

                else:

                    print(
                        "Embedding loaded from Redis "
                        f"for question: {question}"
                    )

                timer.stop("Embedding")

                # -----------------------------
                # Load Chunks
                # -----------------------------
                chunks = (
                    await self.chunk_service
                    .get_chunks_with_embeddings(
                        document_ids
                    )
                )

            # -----------------------------
            # Results
            # -----------------------------
            results = []

            # -----------------------------
            # Global Retrieval
            # -----------------------------
            if "GLOBAL" in retrieval_scopes:

                timer.start("Metadata Filter")

                filtered_chunks = (
                    self.metadata_filter_service.filter(
                        question=question,
                        chunks=chunks,
                    )
                )

                timer.stop("Metadata Filter")

                timer.start("Global Retrieval")

                global_results = await self._search_global(
                    question=question,
                    query_embedding=query_embedding,
                    chunks=filtered_chunks,
                    top_k=top_k,
                )

                timer.stop("Global Retrieval")

                results.extend(
                    global_results
                )

            # -----------------------------
            # Per Document Retrieval
            # -----------------------------
            if "PER_DOCUMENT" in retrieval_scopes:

                timer.start(
                    "Per Document Retrieval"
                )

                per_document_results = (
                    await self._search_per_document(
                        question=question,
                        query_embedding=query_embedding,
                        chunks=chunks,
                        top_k=top_k,
                    )
                )

                timer.stop(
                    "Per Document Retrieval"
                )

                results.extend(
                    per_document_results
                )

            # -----------------------------
            # Remove Duplicate Chunks
            # -----------------------------
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

            # -----------------------------
            # Context Compression
            # -----------------------------
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

                # -----------------------------
                # Token Budget
                # -----------------------------
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

            # -----------------------------
            # No Context
            # -----------------------------
            if (
                not results
                and not metadata_context
            ):

                timer.print()

                return {
                    "answer": (
                        "I couldn't find relevant "
                        "information in the uploaded "
                        "documents."
                    ),
                    "sources": [],
                }

            # -----------------------------
            # Build Context
            # -----------------------------
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
                        f"Document: "
                        f"{chunk.document_name}\n"
                        f"Page: "
                        f"{chunk.page_number}\n"
                        f"Chunk: "
                        f"{chunk.chunk_index}\n"
                        f"Content:\n"
                        f"{chunk.text}\n\n"
                    )

            # -----------------------------
            # Prompt Builder
            # -----------------------------
            timer.start(
                "Prompt Build"
            )

            prompt = self.prompt_builder.build(
                history=history or [],
                summary=summary,
                context=context,
                question=question,
            )

            timer.stop(
                "Prompt Build"
            )

            # -----------------------------
            # LLM
            # -----------------------------
            timer.start("LLM")

            response = (
                await self.ai_service.answer_question(
                    prompt=prompt,
                )
            )

            answer = response["answer"]

            timer.stop("LLM")

            # -----------------------------
            # AI Usage
            # -----------------------------
            await self.ai_usage.log(
                user_id=owner_id,
                session_id=session_id,
                document_id=(
                    document_ids[0]
                    if len(document_ids) == 1
                    else None
                ),
                endpoint="chat",
                prompt_tokens=response[
                    "prompt_tokens"
                ],
                completion_tokens=response[
                    "completion_tokens"
                ],
                latency_ms=response[
                    "latency_ms"
                ],
            )

            timer.print()

            # -----------------------------
            # Sources
            # -----------------------------
            sources = [
                {
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
                }
                for result in results
            ]

            return {
                "answer": answer,
                "sources": sources,
            }

        except SearchException:
            raise

        except Exception as exception:

            raise SearchException(
                str(exception)
            ) from exception