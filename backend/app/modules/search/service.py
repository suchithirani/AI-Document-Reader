from app.core.config import settings

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
class SearchService:

    def __init__(self, db):

        self.chunk_service = DocumentChunkService(db)

        self.embedding_service = GeminiEmbedding()

        self.vector_service = VectorSearchService()

        self.bm25_service = BM25SearchService()

        self.prompt_builder = PromptBuilder()

        self.context_compressor_service = ContextCompressor()

        self.token_budget_service = TokenBudgetService()

        self.hybrid_search_service = HybridSearchService()

        self.metadata_filter_service = MetadataFilterService()
        if settings.GENERATION_PROVIDER == "groq":
            self.ai_service = GroqAIService()
        else:
            self.ai_service = GeminiAIService()

    async def search(
        self,
        document_id: str,
        question: str,
        history: list | None = None,
        top_k: int = 5,
    ):

        try:

            timer = PerformanceLogger()

            # -----------------------------
            # Embedding
            # -----------------------------
            timer.start("Embedding")

            query_embedding = (
                await self.embedding_service.create_embedding(
                    question
                )
            )

            chunks = (
                await self.chunk_service.get_chunks_with_embeddings(
                    document_id
                )
            )

            timer.stop("Embedding")

            # -----------------------------
            # Metadata Filter
            # -----------------------------
            timer.start("Metadata Filter")

            chunks = self.metadata_filter_service.filter(
                question=question,
                chunks=chunks,
            )

            timer.stop("Metadata Filter")

            # -----------------------------
            # BM25
            # -----------------------------
            timer.start("BM25")

            bm25_results = self.bm25_service.search(
                question=question,
                chunks=chunks,
                top_k=top_k,
            )

            timer.stop("BM25")

            # -----------------------------
            # Vector Search
            # -----------------------------
            timer.start("Vector Search")

            vector_results = self.vector_service.search(
                query_embedding=query_embedding,
                chunks=chunks,
                top_k=top_k,
            )

            timer.stop("Vector Search")

            # -----------------------------
            # Hybrid Merge
            # -----------------------------
            timer.start("Hybrid Merge")

            results = self.hybrid_search_service.merge(
                vector_results=vector_results,
                keyword_results=bm25_results,
                top_k=top_k,
            )

            timer.stop("Hybrid Merge")

            # -----------------------------
            # Context Compression
            # -----------------------------
            timer.start("Context Compressor")

            results = self.context_compressor_service.compress(
                results
            )

            timer.stop("Context Compressor")

            # -----------------------------
            # Token Budget
            # -----------------------------
            timer.start("Token Budget")

            results = self.token_budget_service.apply(
                results
            )

            timer.stop("Token Budget")

            if not results:

                timer.print()

                return {
                    "answer": (
                        "I couldn't find relevant information "
                        "in the uploaded document."
                    ),
                    "sources": [],
                }

            # -----------------------------
            # Build Context
            # -----------------------------
            context = ""

            for result in results:

                chunk = result["chunk"]

                context += (
                    f"Page: {chunk.page_number}\n"
                    f"Chunk: {chunk.chunk_index}\n"
                    f"Content:\n"
                    f"{chunk.text}\n\n"
                )

            # -----------------------------
            # Prompt Builder
            # -----------------------------
            timer.start("Prompt Build")

            prompt = self.prompt_builder.build(
                history=history or [],
                context=context,
                question=question,
            )

            timer.stop("Prompt Build")

            # -----------------------------
            # LLM
            # -----------------------------
            timer.start("LLM")

            answer = await self.ai_service.answer_question(
                prompt=prompt,
            )

            timer.stop("LLM")

            timer.print()

            return {
                "answer": answer,
                "sources": [
                    {
                        "page_number": result["chunk"].page_number,
                        "chunk_index": result["chunk"].chunk_index,
                        "score": round(
                            result["score"],
                            4,
                        ),
                        "snippet": (
                            result["chunk"].text[:200] + "..."
                            if len(result["chunk"].text) > 200
                            else result["chunk"].text
                        ),
                    }
                    for result in results
                ],
            }

        except SearchException:
            raise

        except Exception as exception:

            raise SearchException(
                str(exception)
            ) from exception