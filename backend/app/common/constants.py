"""
Application constants.
"""

from enum import StrEnum


class Environment(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SupportedFileType(StrEnum):
    PDF = ".pdf"
    PNG = ".png"
    JPG = ".jpg"
    JPEG = ".jpeg"
    WEBP = ".webp"
    TIFF = ".tiff"
    BMP = ".bmp"


class CollectionName(StrEnum):
    USERS = "users"
    DOCUMENTS = "documents"
    CHAT_SESSIONS = "chat_sessions"
    OCR_RESULTS = "ocr_results"
    REFRESH_TOKENS = "refresh_tokens"
    REQUEST_LOGS = "request_logs"


DEFAULT_PAGE = 1
DEFAULT_LIMIT = 10
MAX_LIMIT = 100

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

class AuthProvider(StrEnum):
    LOCAL = "local"
    GOOGLE = "google"