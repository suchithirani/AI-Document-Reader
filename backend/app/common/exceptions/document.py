from app.common.exceptions.auth import (
    InternalServerException,
    NotFoundException,
)


class DocumentNotFoundException(
    NotFoundException,
):

    def __init__(
        self,
        message: str = "Document not found.",
    ):
        super().__init__(message)


class OCRException(
    InternalServerException,
):

    def __init__(
        self,
        message: str = "Failed to extract text from document.",
    ):
        super().__init__(message)


class DocumentProcessingException(
    InternalServerException,
):

    def __init__(
        self,
        message: str = "Document processing failed.",
    ):
        super().__init__(message)