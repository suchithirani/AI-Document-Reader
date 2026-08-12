from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import DocumentStatus
from app.common.base_schema import BaseSchema


class DocumentResponse(BaseSchema):
    model_config = ConfigDict(
        populate_by_name=True,
    )

    id: str = Field(alias="_id")

    owner_id: str

    filename: str

    original_filename: str

    mime_type: str

    extension: str

    file_size: int

    file_hash: str | None = None
    
    page_count: int | None = None

    status: DocumentStatus

    progress: int

    created_at: datetime

    updated_at: datetime


class ProcessDocumentsRequest(BaseSchema):
    document_ids: list[str] = Field(
        min_length=1,
    )


class UploadDocumentResponse(BaseSchema):
    documents: list[DocumentResponse]
    count: int
    duplicate_documents: list[str] = []