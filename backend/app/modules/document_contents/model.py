from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentContent(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: str | None = Field(
        default=None,
        alias="_id",
    )

    document_id: str

    page_number: int

    text: str

    created_at: datetime

    updated_at: datetime