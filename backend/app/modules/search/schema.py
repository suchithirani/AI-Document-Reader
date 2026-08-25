from pydantic import BaseModel, Field


class AskQuestionRequest(BaseModel):
    document_id: str = Field(...)
    question: str = Field(
        min_length=1,
        max_length=2000,
    )


class SourceChunk(BaseModel):
    page_number: int
    chunk_index: int
    score: float
    text: str


class AskQuestionResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
