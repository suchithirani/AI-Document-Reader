from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import AuditAction, AuditResource


class AuditLog(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: str | None = Field(
        default=None,
        alias="_id",
    )

    user_id: str | None = None

    action: AuditAction

    resource: AuditResource

    resource_id: str | None = None

    description: str

    metadata: dict = Field(
        default_factory=dict,
    )

    ip_address: str | None = None

    user_agent: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )