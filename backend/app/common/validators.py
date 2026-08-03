import re
from uuid import UUID

from fastapi import UploadFile

from app.common.constants import SupportedFileType


def validate_email(email: str) -> bool:
    """
    Validate email format.
    """
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.fullmatch(pattern, email))


def validate_password(password: str) -> bool:
    """
    Password must contain:
    - Minimum 8 characters
    - One uppercase letter
    - One lowercase letter
    - One digit
    - One special character
    """
    pattern = (
        r"^(?=.*[a-z])"
        r"(?=.*[A-Z])"
        r"(?=.*\d)"
        r"(?=.*[@$!%*?&])"
        r"[A-Za-z\d@$!%*?&]{8,}$"
    )

    return bool(re.fullmatch(pattern, password))


def validate_uuid(value: str) -> bool:
    """
    Validate UUID string.
    """
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def validate_file_extension(file: UploadFile) -> bool:
    """
    Validate uploaded file extension.
    """
    if file.filename is None:
        return False

    allowed_extensions = {
        file_type.value for file_type in SupportedFileType
    }

    extension = "." + file.filename.split(".")[-1].lower()

    return extension in allowed_extensions


def validate_file_size(
    file_size: int,
    max_size: int,
) -> bool:
    """
    Validate uploaded file size.
    """
    return file_size <= max_size