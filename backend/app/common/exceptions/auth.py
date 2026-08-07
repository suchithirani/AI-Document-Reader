from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


import logging

logger = logging.getLogger(__name__)

class BaseAppException(Exception):
    """
    Base exception for application errors.
    """

    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BadRequestException(BaseAppException):
    def __init__(self, message: str = "Bad Request"):
        super().__init__(message, 400)


class UnauthorizedException(BaseAppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, 401)


class ForbiddenException(BaseAppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403)


class NotFoundException(BaseAppException):
    def __init__(self, message: str = "Resource Not Found"):
        super().__init__(message, 404)


class ConflictException(BaseAppException):
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, 409)


class InternalServerException(BaseAppException):
    def __init__(self, message: str = "Internal Server Error"):
        super().__init__(message, 500)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(
        request: Request,
        exc: BaseAppException,
    ):
        request.state.error_message = exc.message
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "path": request.url.path,
                "timestamp": datetime.now().isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        exc: Exception,
    ):
        request.state.error_message = str(exc)
        logger.exception(exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal Server Error",
                "path": request.url.path,
                "timestamp": datetime.now().isoformat(),
            },
        )