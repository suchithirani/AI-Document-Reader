from pydantic import BaseModel, Field

from app.common.base_schema import BaseSchema


class CreateChatSessionRequest(BaseSchema):

    document_ids: list[str] | None = Field(
        default=None,
    )
    collection_id: str | None = Field(
        default=None,
    )


class UpdateChatSessionRequest(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=200,
    )


class ChatSessionResponse(BaseModel):

    id: str

    document_id: str

    title: str

    created_at: str


# ===========================
# Message
# ===========================

class SendMessageRequest(BaseModel):

    question: str = Field(
        min_length=1,
    )
    detail_level: str = Field(
        default="standard",
        description="Complexity level: 'eli5', 'standard', or 'expert'"
    )


class SourceResponse(BaseModel):

    document_name: str
    page_number: int

    chunk_index: int

    score: float

    


class ChatMessageResponse(BaseModel):

    role: str

    content: str

    sources: list[SourceResponse] = []


class ChatHistoryResponse(BaseModel):

    session_id: str

    messages: list[ChatMessageResponse]