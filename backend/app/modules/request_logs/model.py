from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class RequestLog(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: str | None = Field(default=None, alias="_id")

    request_id: str

    user_id: str | None = None

    method: str

    path: str

    query_params: dict = Field(default_factory=dict)

    status_code: int

    success: bool

    error_message: str | None = None

    response_time_ms: float

    ip_address: str | None = None

    user_agent: str | None = None

    request_size: int | None = None

    response_size: int | None = None

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )