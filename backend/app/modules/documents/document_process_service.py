import logging
import time
import asyncio
from app.modules.document_chunks.service import DocumentChunkService
from app.modules.document_contents.service import DocumentContentService
from app.modules.documents.repository import DocumentRepository
from app.ocr.service import OCRService
from app.services.chunking.service import ChunkingService
from app.services.embedding.service import EmbeddingService
from app.common.constants import AuditAction, AuditResource, DocumentStatus
from app.common.exceptions.auth import BadRequestException, BaseAppException, NotFoundException
from app.core.config import settings
from app.modules.audit_logs.service import AuditLogService
from app.common.exceptions.document import DocumentProcessingException
from app.workers.process_lock import (
    WorkerProcessingLockService,
)
from app.modules.documents.content_repository import (
    ProcessedContentRepository,
)
from app.common.utils.datetime import utc_now



logger = logging.getLogger(__name__)

class DocumentProcessingService:

    def __init__(self, db):

        self.repository = DocumentRepository(db)
        self.processed_content_repository = ProcessedContentRepository(db)
        self.document_content_service = DocumentContentService(db)
        self.audit_log_service = AuditLogService(db)
        self.document_chunk_service = DocumentChunkService(db)
        self.embedding_service = EmbeddingService(settings.EMBEDDING_PROVIDER)
        self.chunking_service = ChunkingService()
        self.ocr_service = OCRService()
        self.processing_lock_service = WorkerProcessingLockService()

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
            
            await self.repository.update_status(
                document_id,
                DocumentStatus.READY,
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

        texts = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = (
            await self.embedding_service.create_embeddings(
                texts,
            )
        )

        if len(embeddings) != len(chunks):
            raise DocumentProcessingException(
                "Mismatch between number of chunks and embeddings."
            )

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):

            await self.document_chunk_service.update_embedding(
                document_id=chunk.document_id,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                embedding=embedding,
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
                source_document_id = processed_content.get(
                    "document_id"
                )

                await self._reuse_processed_content(
                    source_document_id=source_document_id,
                    target_document_id=document_id,
                )
                chunks = await self.document_chunk_service.get_chunks(
                    document_id,
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

        await self.document_content_service.delete_document_contents(
            document_id,
        )

        await self.document_chunk_service.delete_chunks(
            document_id,
        )

        # -----------------------------
        # OCR timing
        # -----------------------------

        ocr_start = time.perf_counter()

        pages = await asyncio.to_thread(
            self.ocr_service.extract_text,
            file_path=document.storage_path,
            extension=document.extension,
        )

        logger.info(
            "OCR completed for %s in %.2f seconds",
            document.original_filename,
            time.perf_counter() - ocr_start,
        )

        if not pages:
            raise DocumentProcessingException(
                "No text extracted from document.",
            )

        await self.repository.update_status(
            document_id,
            DocumentStatus.CHUNKING,
        )

        await self.document_content_service.save_pages(
            document_id=document_id,
            pages=pages,
        )

        # -----------------------------
        # Chunking timing
        # -----------------------------

        chunk_start = time.perf_counter()

        save_tasks = []

        for page_number, page_text in enumerate(
            pages,
            start=1,
        ):

            chunks = await asyncio.to_thread(
                self.chunking_service.split_text,
                page_text,
            )

            save_tasks.append(
                self.document_chunk_service.save_chunks(
                    document_id=document_id,
                    page_number=page_number,
                    chunks=chunks,
                )
            )

        await asyncio.gather(*save_tasks)

        logger.info(
            "Chunking completed for %s in %.2f seconds",
            document.original_filename,
            time.perf_counter() - chunk_start,
        )

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

        await self.repository.update_status(
            str(document.id),
            DocumentStatus.READY,
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