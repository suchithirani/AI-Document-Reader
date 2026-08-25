from app.common.exceptions.auth import (
    InternalServerException,
)


class DatabaseException(
    InternalServerException,
):

    def __init__(
        self,
        message: str = "Database operation failed.",
    ):
        super().__init__(message)
