from pydantic import BaseModel


class DocumentChunkResponse(BaseModel):

    document_id: str

    page_number: int

    chunk_index: int

    text: str

    token_count: int