from pydantic import BaseModel, Field
from app.common.base_schema import BaseSchema

class CreateDocumentCollectionRequest(BaseSchema):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(default=None, max_length=500)
    document_ids: list[str] = Field(default_factory=list)

class UpdateDocumentCollectionRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(default=None, max_length=500)
    document_ids: list[str] | None = Field(default=None)

class DocumentCollectionResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    description: str | None = None
    document_ids: list[str]
    document_count: int
    created_at: str
    updated_at: str
