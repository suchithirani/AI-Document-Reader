from app.common.exceptions.auth import BaseAppException


class EmailException(BaseAppException):
    def __init__(self, message: str = "Email sending failed."):
        super().__init__(message, 500)