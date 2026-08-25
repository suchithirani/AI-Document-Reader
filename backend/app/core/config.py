from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from .env
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================
    # Application
    # ==========================
    APP_NAME: str = Field(default="AI Document Reader")
    APP_VERSION: str = Field(default="1.0.0")

    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # ==========================
    # MongoDB
    # ==========================
    MONGODB_URI: str
    DATABASE_NAME: str

    # ==========================
    # JWT
    # ==========================
    JWT_ALGORITHM: str = "HS256"
    JWT_PRIVATE_KEY_PATH: str
    JWT_PUBLIC_KEY_PATH: str
    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==========================
    # Logging
    # ==========================
    LOG_LEVEL: str = Field(default="INFO")

    # ==========================
    # File Upload
    # ==========================
    UPLOAD_DIRECTORY: str = "uploads"

    STORAGE_PROVIDER: str = "local"
    MAX_UPLOAD_SIZE: int = Field(default=20 * 1024 * 1024)
    ALLOWED_EXTENSIONS: str = Field(default="pdf,png,jpg,jpeg")

    # ==========================
    # Vector Database (Qdrant)
    # ==========================
    QDRANT_URL: str = Field(default="")
    QDRANT_PATH: str = Field(default="./storage/qdrant")
    QDRANT_API_KEY: str = Field(default="")
    QDRANT_COLLECTION_NAME: str = Field(default="document_chunks")

    # ==========================
    # AI
    # ==========================

    GEMINI_API_KEY: str = Field(...)

    # Embedding
    EMBEDDING_PROVIDER: str = "gemini-embedding-001"
    EMBEDDING_MODEL: str = "gemini-embedding-001"


    # Text generation
    GENERATION_PROVIDER: str = "groq"
    GENERATION_MODEL: str = "openai/gpt-oss-120b"
    GROQ_API_KEY: str = Field(...)

    # Vision
    VISION_PROVIDER: str = "gemini"
    GEMINI_VISION_MODEL: str = "gemini-3.6-flash"
    GROQ_VISION_MODEL: str = "qwen/qwen3.6-27b"

    # Ollama (Local Air-Gapped Mode)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_GENERATION_MODEL: str = Field(default="llama3.1")
    OLLAMA_EMBEDDING_MODEL: str = Field(default="nomic-embed-text")
    OLLAMA_VISION_MODEL: str = Field(default="llava")

    # redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str = Field(default="")
    REDIS_CACHE_TTL: int = Field(default=3600)
    LOGIN_MAX_ATTEMPTS: int
    LOGIN_LOCK_DURATION: int

    # celery beat cleanup
    TEMP_DIRECTORY: str = "./storage/temp"
    TEMP_FILE_RETENTION_HOURS: int = 24
    AUDIT_LOG_RETENTION_DAYS: int = 90

    #email sending
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    SMTP_USE_TLS: bool = True

    # otp
    OTP_PREFIX: str = "otp"
    OTP_TTL: int = 300
    OTP_COOLDOWN: int = 60

@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
