from datetime import UTC, datetime

from pydantic import BaseModel, Field


class DocumentImage(BaseModel):

    id: str | None = Field(
        default=None,
        alias="_id",
    )

    document_id: str

    page_number: int

    image_index: int

    storage_path: str

    extension: str

    width: int

    height: int

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )