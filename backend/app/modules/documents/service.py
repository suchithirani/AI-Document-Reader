import hashlib
from fastapi.responses import FileResponse

from app.modules.documents.repository import (
    DocumentRepository,
)
from app.workers.document_tasks import (
    process_documents_batch_task,
)
from app.common.exceptions.auth import BaseAppException
from app.services.embedding.service import (
    EmbeddingService,
)

from app.modules.document_chunks.service import (
    DocumentChunkService,
)
from app.services.chunking.service import (
    ChunkingService,
)
from app.services.storage.service import (
    StorageService,
)
from app.modules.audit_logs.service import (
    AuditLogService,
)
from pathlib import Path
from app.modules.document_contents.service import (
    DocumentContentService,
)
from fastapi import Request, UploadFile
from app.common.constants import (
    AuditAction,
    AuditResource,
    DocumentStatus,
)
from app.common.utils.request import get_request_info
from app.common.exceptions.auth import BadRequestException, ForbiddenException, NotFoundException
from app.common.utils.datetime import utc_now
from app.common.validators import (
    validate_content_type,
    validate_file_extension,
    validate_file_size,
    validate_filename,
)
from app.core.config import settings
from app.modules.auth.model import User
from app.modules.documents.model import Document
from app.modules.documents.schema import (
    DocumentResponse,
    UploadDocumentResponse,
)
from app.common.utils.pdf import get_pdf_page_count
from app.ocr.service import OCRService

from app.services.cache.response import ResponseCache
from app.services.cache.processing_lock import ProcessingLockService

class DocumentService:

    def __init__(self, db):
        self.repository = DocumentRepository(db)

        self.storage_service = StorageService(db)

        self.audit_log_service = AuditLogService(db)
        self.document_content_service = DocumentContentService(db)
        self.document_chunk_service = DocumentChunkService(db)
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService(settings.EMBEDDING_PROVIDER)
        self.ocr_service = OCRService()
        self.response_cache = ResponseCache()
        self.processing_lock = ProcessingLockService()

    async def upload_document(
        self,
        http_request: Request,
        current_user: User,
        files: list[UploadFile],
    ) -> UploadDocumentResponse:
        
        if len(files) > 10:
            raise BadRequestException(
                "Maximum 10 files can be uploaded at once."
            )
        uploaded_documents = []
        duplicate_documents = []
        for file in files:

            if not validate_file_extension(file):
                raise BadRequestException(
                    "Unsupported file type."
                )

            if not validate_content_type(file):
                raise BadRequestException(
                    "Unsupported content type."
                )

            file_bytes = await file.read()

            file_size = len(file_bytes)
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            existing_document = (
                await self.repository.get_document_by_hash(
                    owner_id=str(current_user.id),
                    file_hash=file_hash,
                )
            )

            if existing_document is not None:
                duplicate_documents.append(
                    existing_document.original_filename
                )
                uploaded_documents.append(
                    DocumentResponse.model_validate(
                        existing_document.model_dump(
                            by_alias=True,
                            exclude={
                                "storage_provider",
                                "storage_path",
                                "deleted_at",
                            },
                        )
                    )
                )

                continue

            if not validate_file_size(
                file_size,
                settings.MAX_UPLOAD_SIZE,
            ):
                raise BadRequestException(
                    "File exceeds maximum upload size."
                )

            await file.seek(0)

            filename, storage_path = (
                await self.storage_service.save_file(file)
            )

            now = utc_now()
            page_count = None

            if file.content_type == "application/pdf":
                page_count = get_pdf_page_count(storage_path)

            elif file.content_type in (
                "image/png",
                "image/jpeg",
            ):
                page_count = 1

            document = Document(
                owner_id=str(current_user.id),
                filename=filename,
                original_filename=file.filename,
                storage_provider=settings.STORAGE_PROVIDER,
                storage_path=storage_path,
                mime_type=file.content_type,
                extension=Path(file.filename).suffix.lower(),
                page_count=page_count,
                file_size=file_size,
                file_hash=file_hash,
                status=DocumentStatus.UPLOADED,
                created_at=now,
                updated_at=now,
            )

            created_document = (
                await self.repository.create_document(
                    document.model_dump(
                        by_alias=True,
                        exclude_none=True,
                    )
                )
            )
            uploaded_documents.append(
                DocumentResponse.model_validate(
                    created_document.model_dump(
                        by_alias=True,
                        exclude={
                            "storage_provider",
                            "storage_path",
                            "deleted_at",
                            "file_hash",
                        },
                    )
                )
            )
            
            await self.response_cache.delete(
                f"documents:{current_user.id}:0:20"
            )

            ip_address, user_agent = get_request_info(
                    http_request
                )

            await self.audit_log_service.create_log(
                user_id=str(current_user.id),
                action=AuditAction.DOCUMENT_UPLOAD,
                resource=AuditResource.DOCUMENT,
                resource_id=str(created_document.id),
                description=f"{len(uploaded_documents)} documents uploaded successfully.",
                metadata={
                    "count": len(uploaded_documents),
                    "documents": [
                        {
                            "filename": doc.original_filename,
                            "mime_type": doc.mime_type,
                            "file_size": doc.file_size,
                        }
                        for doc in uploaded_documents
                    ],
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return UploadDocumentResponse(
            documents=uploaded_documents,
            count=len(uploaded_documents),
            duplicate_documents=duplicate_documents
        )

    async def get_documents(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
    ) -> list[DocumentResponse]:

        cache_key = (
            f"documents:{current_user.id}:"
            f"{skip}:{limit}"
        )

        cached = await self.response_cache.get(
            cache_key
        )

        if cached is not None:

            print("Documents loaded from Redis.")

            return [
                DocumentResponse.model_validate(item)
                for item in cached
            ]

        documents = await self.repository.get_documents_by_owner(
            owner_id=str(current_user.id),
            skip=skip,
            limit=limit,
        )

        result = [
            DocumentResponse.model_validate(
                document.model_dump(
                    by_alias=True,
                    exclude={
                        "storage_provider",
                        "deleted_at",
                        "storage_path",
                    },
                )
            )
            for document in documents
        ]

        # Store JSON-serializable dictionaries
        await self.response_cache.set(
            cache_key,
            [
                document.model_dump(
                    by_alias=True,
                    mode="json",
                )
                for document in result
            ],
        )

        print("Documents cached.")

        return result

    async def get_document(
        self,
        current_user: User,
        document_id: str,
    ) -> DocumentResponse:

        document = await self.repository.get_document_by_id(
            document_id
        )

        if document is None:
            raise NotFoundException(
                "Document not found."
            )

        if document.owner_id != str(current_user.id):
            raise ForbiddenException(
                "You are not allowed to access this document."
            )

        return DocumentResponse.model_validate(
            document.model_dump(
                by_alias=True,
                exclude={
                    "storage_provider",
                    "deleted_at",
                    "storage_path",
                },
            )
        )
    
    async def delete_document(
        self,
        http_request: Request,
        current_user: User,
        document_id: str,
    ) -> dict:

        document = await self.repository.get_document_by_id(
            document_id
        )

        if document is None:
            raise NotFoundException(
                "Document not found."
            )

        if document.owner_id != str(current_user.id):
            raise ForbiddenException(
                "You are not allowed to delete this document."
            )

        await self.storage_service.delete_file(
            document.storage_path
        )

        await self.repository.soft_delete(
            document_id
        )
        await self.response_cache.delete(
            f"documents:{current_user.id}:0:20"
        )

        ip_address, user_agent = get_request_info(
            http_request
        )

        await self.audit_log_service.create_log(
            user_id=str(current_user.id),
            action=AuditAction.DOCUMENT_DELETE,
            resource=AuditResource.DOCUMENT,
            resource_id=document_id,
            description="Document deleted successfully.",
            metadata={
                "filename": document.original_filename,
                "mime_type": document.mime_type,
                "file_size": document.file_size,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "message": "Document deleted successfully."
    }

    async def count_documents(
        self,
        current_user: User,
    ) -> int:

        return await self.repository.count_documents(
            owner_id=str(current_user.id),
        )

    async def download_document(
        self,
        current_user: User,
        document_id: str,
    ) -> FileResponse:

        document = await self.repository.get_document_by_id(
            document_id
        )

        if document is None:
            raise NotFoundException(
                "Document not found."
            )

        if document.owner_id != str(current_user.id):
            raise ForbiddenException(
                "You are not allowed to access this document."
            )

        file_path = self.storage_service.get_file_path(
            document.storage_path
        )

        return FileResponse(
            path=file_path,
            filename=document.original_filename,
            media_type=document.mime_type,
        )

    async def process_documents(
        self,
        http_request: Request,
        current_user: User,
        document_ids: list[str],
    ):
        document_ids = list(dict.fromkeys(document_ids))
        queued_documents = []

        for document_id in document_ids:

            document = await self.repository.get_document_by_id(
                document_id,
            )

            if document is None:
                raise NotFoundException(
                    f"Document {document_id} not found.",
                )

            if document.owner_id != str(current_user.id):
                raise ForbiddenException(
                    "You are not allowed to process this document.",
                )

            if document.status in (
                DocumentStatus.QUEUED,
                DocumentStatus.OCR_PROCESSING,
                DocumentStatus.CHUNKING,
                DocumentStatus.EMBEDDING,
                DocumentStatus.READY,
            ):
                continue

            await self.repository.update_status(
                document_id,
                DocumentStatus.QUEUED,
            )

            queued_documents.append(document_id)

        if not queued_documents:

            return {
                "queued_documents": [],
                "count": 0,
            }

        process_documents_batch_task.delay(
            owner_id=str(current_user.id),
            document_ids=queued_documents,
        )

        ip_address, user_agent = get_request_info(
            http_request,
        )

        await self.audit_log_service.create_log(
            user_id=str(current_user.id),
            action=AuditAction.DOCUMENT_PROCESS,
            resource=AuditResource.DOCUMENT,
            description="Queued multiple documents for processing.",
            metadata={
                "document_count": len(queued_documents),
                "document_ids": queued_documents,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "queued_documents": queued_documents,
            "count": len(queued_documents),
        }    