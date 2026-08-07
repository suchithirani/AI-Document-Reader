from app.common.exceptions.auth import (
    InternalServerException,
)


class EmbeddingException(
    InternalServerException,
):

    def __init__(
        self,
        message: str = "Embedding generation failed.",
    ):
        super().__init__(message)


class AIResponseException(
    InternalServerException,
):

    def __init__(
        self,
        message: str = "AI response generation failed.",
    ):
        super().__init__(message)