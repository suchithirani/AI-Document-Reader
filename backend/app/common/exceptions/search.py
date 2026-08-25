from app.common.exceptions.auth import (
    InternalServerException,
)


class SearchException(
    InternalServerException,
):

    def __init__(
        self,
        message: str = "Search failed.",
    ):
        super().__init__(message)


class VectorSearchException(
    InternalServerException,
):

    def __init__(
        self,
        message: str = "Vector search failed.",
    ):
        super().__init__(message)
