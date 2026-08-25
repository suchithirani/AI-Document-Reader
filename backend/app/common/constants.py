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


class QueryIntent(StrEnum):
    GENERAL = "general"
    FACTUAL = "factual"
    EXPLANATION = "explanation"
    SUMMARY = "summary"
    COMPARISON = "comparison"
    EXTRACTION = "extraction"
    TOC = "toc"


class QueryScope(StrEnum):
    GLOBAL = "global"
    TARGETED = "targeted"
    PAGE = "page"


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
    DOCUMENT_CHUNKS = "document_chunks"
    CHAT_MESSAGES = "chat_messages"
    CHAT_SESSION_DOCUMENTS = "chat_session_documents"
    ANALYTICS_DAILY = "analytics_daily"
    AI_USAGE_LOGS = "ai_usage_logs"
    SYSTEM_METRICS = "system_metrics"
    DOCUMENT_COLLECTIONS = "document_collections"
    USER_MEMORIES = "user_memories"
    PROCESSED_DOCUMENT_CONTENT = "processed_document_content"
    DOCUMENT_IMAGES = "document_images"

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
    EMAIL_VERIFY = "EMAIL_VERIFY"

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

    UPLOADED = "UPLOADED"
    OCR_PROCESSING = "OCR_PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    DELETED = "DELETED"
    QUEUED = "QUEUED"

DOCUMENT_PROGRESS = {
    DocumentStatus.UPLOADED: 0,
    DocumentStatus.QUEUED: 5,
    DocumentStatus.OCR_PROCESSING: 10,
    DocumentStatus.CHUNKING: 40,
    DocumentStatus.EMBEDDING: 75,
    DocumentStatus.READY: 100,
    DocumentStatus.FAILED: 0,
}

class ChatRole(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"

# OCR Quality Metrics Warning Thresholds
OCR_QUALITY_WARNING_THRESHOLD = 60.0
OCR_QUALITY_CRITICAL_THRESHOLD = 30.0
