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
    PROCESSED = "processed"
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
    AUDIT_LOGS = "audit_logs"
    DOCUMENT_CONTENTS = "document_contents"


DEFAULT_PAGE = 1
DEFAULT_LIMIT = 10
MAX_LIMIT = 100

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

class AuthProvider(StrEnum):
    LOCAL = "local"
    GOOGLE = "google"

class AuditAction(StrEnum):
    REGISTER = "REGISTER"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CHANGE_PASSWORD = "CHANGE_PASSWORD"
    REFRESH_TOKEN = "REFRESH_TOKEN"
    
    DOCUMENT_PROCESS = "DOCUMENT_PROCESS"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    DOCUMENT_UPDATE = "DOCUMENT_UPDATE"

    OCR_START = "OCR_START"
    OCR_COMPLETE = "OCR_COMPLETE"

    CHAT_CREATED = "CHAT_CREATED"
    CHAT_DELETED = "CHAT_DELETED"

class AuditResource(StrEnum):
    AUTH = "AUTH"
    DOCUMENT = "DOCUMENT"
    OCR = "OCR"
    CHAT = "CHAT"
    PROFILE = "PROFILE"

class DocumentStatus(StrEnum):
    UPLOADING = "UPLOADING"

    UPLOADED = "UPLOADED"

    OCR_PROCESSING = "OCR_PROCESSING"

    OCR_COMPLETED = "OCR_COMPLETED"

    AI_PROCESSING = "AI_PROCESSING"

    READY = "READY"

    FAILED = "FAILED"

    DELETED = "DELETED"