from datetime import UTC, datetime

from pydantic import ConfigDict, Field

from app.common.base_schema import BaseSchema


class AIUsageLog(BaseSchema):

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: str | None = Field(
        default=None,
        alias="_id",
    )

    user_id: str | None = None

    session_id: str | None = None

    document_id: str | None = None

    provider: str

    model: str

    endpoint: str

    prompt_tokens: int

    completion_tokens: int

    total_tokens: int

    estimated_cost: float

    latency_ms: float

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
