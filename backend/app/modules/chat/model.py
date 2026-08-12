from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import ChatRole


class ChatSession(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: str | None = Field(
        default=None,
        alias="_id",
    )
    owner_id: str
    title: str
    title_generated: bool = False
    summary: str | None = None

    summary_updated_at: datetime | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    deleted_at: datetime | None = None


class ChatMessage(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
    id: str | None = Field(
        default=None,
        alias="_id",
    )
    session_id: str
    role: ChatRole
    content: str
    sources: list[dict] = Field(
        default_factory=list,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )