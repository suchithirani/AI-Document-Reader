from app.common.exceptions.auth import (
    InternalServerException,
)


class FileStorageException(
    InternalServerException,
):

    def __init__(
        self,
        message: str = "File storage operation failed.",
    ):
        super().__init__(message)
