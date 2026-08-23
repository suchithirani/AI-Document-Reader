from datetime import UTC, datetime
from pydantic import BaseModel, ConfigDict, Field

class DocumentCollection(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: str | None = Field(
        default=None,
        alias="_id",
    )
    owner_id: str
    name: str
    description: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    deleted_at: datetime | None = None
