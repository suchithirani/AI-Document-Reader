from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionDocument(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: str | None = Field(
        default=None,
        alias="_id",
    )

    session_id: str

    document_id: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
