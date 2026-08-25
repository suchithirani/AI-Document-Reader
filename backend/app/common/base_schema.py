from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """
    Base schema inherited by all request and response models.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class MessageResponse(BaseSchema):
    success: bool = True
    message: str


class ResponseSchema(BaseSchema, Generic[T]):
    success: bool = True
    message: str
    data: T | None = None


class ErrorResponse(BaseSchema):
    success: bool = False
    message: str
    path: str
    timestamp: datetime


class Pagination(BaseSchema):
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    pages: int = Field(..., ge=0)


class PaginatedResponse(BaseSchema, Generic[T]):
    success: bool = True
    data: list[T]
    pagination: Pagination
