from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import DocumentStatus


class Document(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: str | None = Field(
        default=None,
        alias="_id",
    )
    owner_id: str
    filename: str
    original_filename: str
    storage_provider: str
    storage_path: str
    mime_type: str
    extension: str
    file_size: int
    page_count: int | None = None
    status: DocumentStatus = (
        DocumentStatus.UPLOADED
    )
    progress: int = Field(default=0,ge=0,le=100,)
    file_hash: str | None = None
    description: str | None = None
    document_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    extracted_metadata: dict = Field(default_factory=dict)
    version: int = Field(default=1)
    version_group_id: str | None = None
    is_latest: bool = True
    ocr_quality_score: float | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    deleted_at: datetime | None = None
