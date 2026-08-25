import asyncio
import logging
import time
from uuid import uuid4

from app.common.constants import AuditAction, AuditResource, DocumentStatus
from app.common.exceptions.auth import BadRequestException, BaseAppException, NotFoundException
from app.common.exceptions.document import DocumentProcessingException
from app.common.utils.datetime import utc_now
from app.core.config import settings
from app.modules.audit_logs.service import AuditLogService
from app.modules.document_chunks.service import DocumentChunkService
from app.modules.document_contents.service import DocumentContentService
from app.modules.document_images.service import DocumentImageService
from app.modules.documents.content_repository import (
    ProcessedContentRepository,
)
from app.modules.documents.repository import DocumentRepository
from app.ocr.service import OCRService
from app.services.cache.response import ResponseCache
from app.services.chunking.service import ChunkingService
from app.services.document_images.pdf_image_extractor import PDFImageExtractor
from app.services.embedding.service import EmbeddingService
from app.services.storage.service import StorageService
from app.workers.process_lock import (
    WorkerProcessingLockService,
)

logger = logging.getLogger(__name__)

class DocumentProcessingService:

    def __init__(self, db):

        self.repository = DocumentRepository(db)
        self.processed_content_repository = ProcessedContentRepository(db)
        self.document_content_service = DocumentContentService(db)
        self.audit_log_service = AuditLogService(db)
        self.document_chunk_service = DocumentChunkService(db)
        self.storage_service = StorageService(db)
        self.embedding_service = EmbeddingService(settings.EMBEDDING_PROVIDER)
        self.chunking_service = ChunkingService()
        self.ocr_service = OCRService()
        self.processing_lock_service = WorkerProcessingLockService()
        self.pdf_image_extractor = PDFImageExtractor()
        from app.repositories.qdrant_repository import QdrantRepository
        self.qdrant_repo = QdrantRepository()
        self.document_image_service = DocumentImageService(db)
        self.response_cache = ResponseCache()

    async def process_documents(
        self,
        owner_id: str,
        document_ids: list[str],
    ):

        all_chunks = []
        processed_documents = []
        document_ids = list(dict.fromkeys(document_ids))
        if not document_ids:
            raise BadRequestException(
                "At least one document is required."
            )
        try:

            results = await asyncio.gather(
                *[
                    self._prepare_document(
                        owner_id=owner_id,
                        document_id=document_id,
                    )
                    for document_id in document_ids
                ]
            )

            for result in results:

                document, page_count, chunks = result

                processed_documents.append(
                    {
                        "document": document,
                        "page_count": page_count,
                        "chunks": chunks,
                    }
                )

                all_chunks.extend(chunks)

            await self._generate_embeddings(
                all_chunks,
            )

            for item in processed_documents:

                await self._finish_document(
                    owner_id=owner_id,
                    document=item["document"],
                    page_count=item["page_count"],
                    chunks=item["chunks"],
                )

            # Trigger Proactive Insights analysis after successful batch processing
            from app.workers.ai_tasks import generate_proactive_insights_task
            generate_proactive_insights_task.delay(
                owner_id=owner_id,
                document_ids=document_ids,
            )

        except Exception as exception:

            logger.exception(
                "Batch document processing failed.",
            )

            for document_id in document_ids:

                try:

                    await self.repository.update_status(
                        document_id,
                        DocumentStatus.FAILED,
                    )

                    await self.response_cache.delete(
                        f"documents:{owner_id}:0:20"
                    )

                except Exception:

                    logger.exception(
                        "Failed to mark document %s as FAILED.",
                        document_id,
                    )

            if isinstance(
                exception,
                BaseAppException,
            ):
                raise

            raise DocumentProcessingException(
                str(exception),
            ) from exception

        finally:

            for document_id in document_ids:

                try:

                    await self.processing_lock_service.release(
                        document_id,
                    )

                except Exception:

                    logger.exception(
                        "Failed to release lock for %s.",
                        document_id,
                    )

            await self.processing_lock_service.close()

    async def process(
    self,
    owner_id: str,
    document_id: str,
):

        try:

            (
                document,
                page_count,
                chunks,
            ) = await self._prepare_document(
                owner_id,
                document_id,
            )

            await self._generate_embeddings(
                chunks,
            )
            embedded_chunks = (
                await self.document_chunk_service
                .get_chunks_with_embeddings(
                    [document_id],
                )
            )

            if len(embedded_chunks) != len(chunks):
                raise DocumentProcessingException(
                    f"Embedding verification failed for "
                    f"document {document_id}: "
                    f"{len(embedded_chunks)}/{len(chunks)} "
                    f"chunks have embeddings."
                )
            if document.file_hash:

                await self.processed_content_repository.create(
                    {
                    "file_hash": document.file_hash,
                    "source_document_id": document_id,
                    "document_id": document_id,
                    "page_count": page_count,
                    "created_at": utc_now(),
                    "updated_at": utc_now(),
                    }
                )


            await self._finish_document(
                owner_id,
                document,
                page_count,
                chunks,
            )

        except Exception as exception:

            await self.repository.update_status(
                document_id,
                DocumentStatus.FAILED,
            )

            if isinstance(
                exception,
                BaseAppException,
            ):
                raise

            raise DocumentProcessingException(
                str(exception),
            ) from exception

        finally:

            await self.processing_lock_service.release(
                document_id,
            )

            await self.processing_lock_service.close()

    async def _generate_embeddings(
        self,
        chunks,
    ):

        if not chunks:
            return

        print("\n========== EMBEDDING INPUT DEBUG ==========")
        print("Chunks received:", len(chunks))

        print(
            "Chunk locations:",
            [
                (
                    chunk.page_number,
                    chunk.chunk_index,
                )
                for chunk in chunks
            ],
        )

        texts = [
            chunk.text
            for chunk in chunks
        ]

        print(
            "Texts sent to embedding:",
            len(texts),
        )

        print("===========================================\n")

        embeddings = (
            await self.embedding_service.create_embeddings(
                texts,
            )
        )

        print("\n========== EMBEDDING OUTPUT DEBUG ==========")
        print(
            "Embeddings returned:",
            len(embeddings),
        )
        print("Expected:", len(chunks))
        print("============================================\n")

        if len(embeddings) != len(chunks):
            raise DocumentProcessingException(
                f"Embedding mismatch: "
                f"{len(chunks)} chunks -> "
                f"{len(embeddings)} embeddings"
            )

        successful_updates = 0
        failed_updates = 0

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):
            chunk.embedding = embedding

            updated = await self.document_chunk_service.update_embedding(
                document_id=chunk.document_id,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                embedding=embedding,
            )

            if updated is None:

                failed_updates += 1

                print(
                    "❌ UPDATE FAILED:",
                    chunk.page_number,
                    chunk.chunk_index,
                )

            else:

                successful_updates += 1

        print("\n========== EMBEDDING UPDATE DEBUG ==========")
        print("Successful updates:", successful_updates)
        print("Failed updates:", failed_updates)
        print("============================================\n")

        if successful_updates != len(chunks):
            raise DocumentProcessingException(
                f"Embedding update failed: "
                f"{successful_updates}/{len(chunks)} chunks updated."
            )

        logger.info(
            "Generated embeddings for %d chunks in one request.",
            len(texts),
        )

    async def _prepare_document(
        self,
        owner_id: str,
        document_id: str,
    ):

        document = await self.repository.get_document_by_id(
            document_id,
        )

        if document is None:
            raise NotFoundException(
                "Document not found.",
            )

        # ---------------------------------
        # Reuse processed content
        # ---------------------------------

        if document.file_hash:

            processed_content = (
                await self.processed_content_repository.get_by_hash(
                    document.file_hash
                )
            )

            if processed_content is not None:

                logger.info(
                    "Reusing processed content for %s",
                    document.original_filename,
                )

                source_document_id = (
                    processed_content.get("document_id")
                )

                await self._reuse_processed_content(
                    source_document_id=source_document_id,
                    target_document_id=document_id,
                )

                chunks = (
                    await self.document_chunk_service.get_chunks(
                        document_id,
                    )
                )

                return (
                    document,
                    processed_content["page_count"],
                    chunks,
                )

        logger.info("==========")
        logger.info(
            "Processing %s",
            document.original_filename,
        )
        logger.info("==========")

        await self.repository.update_status(
            document_id,
            DocumentStatus.OCR_PROCESSING,
        )

        # ---------------------------------
        # Remove old processed data
        # ---------------------------------

        await self.document_content_service.delete_document_contents(
            document_id,
        )

        await self.document_chunk_service.delete_chunks(
            document_id,
        )

        await self.document_image_service.delete_document_images(
            document_id,
        )

        # ---------------------------------
        # OCR
        # ---------------------------------

        ocr_start = time.perf_counter()

        pages = await asyncio.to_thread(
            self.ocr_service.extract_text,
            file_path=document.storage_path,
            extension=document.extension,
        )

        if not pages:
            raise DocumentProcessingException(
                "No text extracted from document.",
            )

        logger.info(
            "OCR completed for %s in %.2f seconds",
            document.original_filename,
            time.perf_counter() - ocr_start,
        )

        # ---------------------------------
        # OCR Quality Check
        # ---------------------------------
        from app.ocr.quality import calculate_document_quality
        quality_score = await asyncio.to_thread(
            calculate_document_quality,
            file_path=document.storage_path,
            extension=document.extension,
        )
        await self.repository.update(
            document_id,
            {"ocr_quality_score": quality_score}
        )
        document.ocr_quality_score = quality_score

        # ---------------------------------
        # PDF Image Extraction
        # ---------------------------------

        if document.extension.lower() == ".pdf":

            image_start = time.perf_counter()

            images = await asyncio.to_thread(
                self.pdf_image_extractor.extract_images,
                document.storage_path,
            )

            logger.info(
                "Extracted %s images from %s",
                len(images),
                document.original_filename,
            )

            image_records = []

            for image in images:

                filename = (
                    f"{document_id}_"
                    f"page_{image['page_number']}_"
                    f"image_{image['image_index']}_"
                    f"{uuid4().hex}."
                    f"{image['extension']}"
                )

                storage_path = (
                    await self.storage_service.save_bytes(
                        data=image["image_bytes"],
                        filename=filename,
                    )
                )

                image_records.append(
                    {
                        "document_id": document_id,
                        "page_number": image[
                            "page_number"
                        ],
                        "image_index": image[
                            "image_index"
                        ],
                        "storage_path": storage_path,
                        "extension": image[
                            "extension"
                        ],
                        "width": image["width"],
                        "height": image["height"],
                    }
                )

            if image_records:

                await self.document_image_service.save_images(
                    images=image_records,
                )

            logger.info(
                "Image extraction completed for %s "
                "in %.2f seconds",
                document.original_filename,
                time.perf_counter() - image_start,
            )

        # ---------------------------------
        # Chunking
        # ---------------------------------

        await self.repository.update_status(
            document_id,
            DocumentStatus.CHUNKING,
        )

        await self.document_content_service.save_pages(
            document_id=document_id,
            pages=pages,
        )

        chunk_start = time.perf_counter()

        async def process_page_chunk(page_num, page_txt):
            page_chunks = await asyncio.to_thread(
                self.chunking_service.split_text,
                page_txt,
            )
            if page_chunks:
                await self.document_chunk_service.save_chunks(
                    document_id=document_id,
                    page_number=page_num,
                    chunks=page_chunks,
                )

        chunk_tasks = [
            process_page_chunk(page_number, page_text)
            for page_number, page_text in enumerate(pages, start=1)
        ]

        if chunk_tasks:
            await asyncio.gather(*chunk_tasks)

        logger.info(
            "Chunking completed for %s in %.2f seconds",
            document.original_filename,
            time.perf_counter() - chunk_start,
        )

        # ---------------------------------
        # Embedding
        # ---------------------------------

        await self.repository.update_status(
            document_id,
            DocumentStatus.EMBEDDING,
        )

        chunks = await self.document_chunk_service.get_chunks(
            document_id,
        )

        return (
            document,
            len(pages),
            chunks,
        )

    async def _reuse_processed_content(
        self,
        source_document_id: str,
        target_document_id: str,
    ):

        page_count = (
            await self.document_content_service.copy_pages(
                source_document_id=source_document_id,
                target_document_id=target_document_id,
            )
        )

        chunk_count = (
            await self.document_chunk_service.copy_chunks(
                source_document_id=source_document_id,
                target_document_id=target_document_id,
            )
        )

        if page_count == 0 or chunk_count == 0:

            raise DocumentProcessingException(
                "Processed content is incomplete."
            )

        await self.repository.update_status(
            target_document_id,
            DocumentStatus.READY,
        )

    async def _finish_document(
        self,
        owner_id: str,
        document,
        page_count: int,
        chunks,
    ):

        if chunks:
            self.qdrant_repo.upsert_chunks(chunks, owner_id)
            logger.info("Synced %d chunks to Qdrant.", len(chunks))

        await self.repository.update_status(
            str(document.id),
            DocumentStatus.READY,
        )

        from app.workers.ai_tasks import extract_document_metadata_task
        extract_document_metadata_task.delay(
            owner_id=owner_id,
            document_id=str(document.id),
        )

        await self.response_cache.delete(
            f"documents:{owner_id}:0:20"
        )

        await self.audit_log_service.create_log(
            user_id=owner_id,
            action=AuditAction.DOCUMENT_PROCESS,
            resource=AuditResource.DOCUMENT,
            resource_id=str(document.id),
            description="Document processed successfully.",
            metadata={
                "pages": page_count,
                "chunks": len(chunks),
            },
        )

        logger.info(
            "Finished %s",
            document.original_filename,
        )
