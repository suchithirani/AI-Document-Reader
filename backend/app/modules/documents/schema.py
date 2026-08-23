from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

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

    description: str | None = None
    document_type: str | None = None
    tags: list[str] = []
    extracted_metadata: dict = {}
    version: int = 1
    version_group_id: str | None = None
    is_latest: bool = True
    ocr_quality_score: float | None = None
    ocr_quality_warning: bool = False

    @model_validator(mode="before")
    @classmethod
    def compute_quality_warnings(cls, data):
        if isinstance(data, dict):
            score = data.get("ocr_quality_score")
            if score is None:
                score = data.get("ocrQualityScore")
            
            if score is not None:
                from app.common.constants import OCR_QUALITY_WARNING_THRESHOLD
                data["ocr_quality_warning"] = score < OCR_QUALITY_WARNING_THRESHOLD
        return data


class ProcessDocumentsRequest(BaseSchema):
    document_ids: list[str] = Field(
        min_length=1,
    )


class UploadDocumentResponse(BaseSchema):
    documents: list[DocumentResponse]
    count: int
    duplicate_documents: list[str] = []