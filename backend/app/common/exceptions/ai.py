from app.common.exceptions.auth import (
    UnauthorizedException,
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


class AIAuthenticationException(
    UnauthorizedException,
):

    def __init__(
        self,
        message: str = "AI provider API key is invalid or expired.",
    ):
        super().__init__(message)