from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentChunk(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,
    )

    id: str | None = Field(
        default=None,
        alias="_id",
    )

    document_id: str
    document_name: str | None = None
    page_number: int
    chunk_index: int
    text: str
    token_count: int
    word_count: int
    character_count: int

    has_numbers: bool = False
    has_table: bool = False
    has_email: bool = False
    has_url: bool = False
    embedding: list[float] | None = None

    created_at: datetime

    updated_at: datetime
