from pydantic import BaseModel


class DocumentContentResponse(BaseModel):
    document_id: str

    page_number: int

    text: str
