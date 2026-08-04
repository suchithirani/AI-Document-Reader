from fastapi.responses import FileResponse

from app.modules.documents.repository import (
    DocumentRepository,
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
from app.common.exception import BadRequestException, ForbiddenException, NotFoundException
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


class DocumentService:

    def __init__(self, db):
        self.repository = DocumentRepository(db)

        self.storage_service = StorageService()

        self.audit_log_service = AuditLogService(db)
        self.document_content_service = DocumentContentService(db)

        self.ocr_service = OCRService()
    async def upload_document(
        self,
        http_request: Request,
        current_user: User,
        file: UploadFile,
    ) -> UploadDocumentResponse:

        if not validate_filename(file):
            raise BadRequestException(
                "Filename is required."
            )

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

        ip_address, user_agent = get_request_info(
                http_request
            )

        await self.audit_log_service.create_log(
            user_id=str(current_user.id),
            action=AuditAction.DOCUMENT_UPLOAD,
            resource=AuditResource.DOCUMENT,
            resource_id=str(created_document.id),
            description="Document uploaded successfully.",
            metadata={
                "filename": created_document.original_filename,
                "mime_type": created_document.mime_type,
                "file_size": created_document.file_size,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return UploadDocumentResponse(
            document=DocumentResponse.model_validate(
                created_document.model_dump(
                    by_alias=True
                )
            )
        )

    async def get_documents(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
    ) -> list[DocumentResponse]:

        documents = await self.repository.get_documents_by_owner(
            owner_id=str(current_user.id),
            skip=skip,
            limit=limit,
        )

        return [
            DocumentResponse.model_validate(
                document.model_dump(
                    by_alias=True,
                )
            )
            for document in documents
        ]

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

    async def process_document(
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
                "You are not allowed to process this document."
            )

        await self.repository.update_status(
            document_id,
            DocumentStatus.OCR_PROCESSING,
        )
        await self.document_content_service.delete_document_contents(
            document_id
        )

        pages = self.ocr_service.extract_text(
            file_path=document.storage_path,
            extension=document.extension,
        )

        await self.document_content_service.save_pages(
            document_id=document_id,
            pages=pages,
        )
        try:

            pages = self.ocr_service.extract_text(
                file_path=document.storage_path,
                extension=document.extension,
            )

            await self.document_content_service.save_pages(
                document_id=document_id,
                pages=pages,
            )

            await self.repository.update_status(
                document_id,
                DocumentStatus.OCR_COMPLETED,
            )

        except Exception:

            await self.repository.update_status(
                document_id,
                DocumentStatus.FAILED,
            )

            raise

        ip_address, user_agent = get_request_info(
            http_request
        )

        await self.audit_log_service.create_log(
            user_id=str(current_user.id),
            action=AuditAction.DOCUMENT_PROCESS,
            resource=AuditResource.DOCUMENT,
            resource_id=document_id,
            description="Document processed successfully.",
            metadata={
                "pages": len(pages),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "document_id": document_id,
            "pages_processed": len(pages),
            "status": DocumentStatus.OCR_COMPLETED,
        }
