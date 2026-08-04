from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import DocumentStatus


class DocumentResponse(BaseModel):
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

    page_count: int | None = None

    status: DocumentStatus

    created_at: datetime

    updated_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]

    total: int


class UploadDocumentResponse(BaseModel):
    document: DocumentResponse