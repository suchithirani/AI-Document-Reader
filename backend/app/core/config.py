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
    MAX_UPLOAD_SIZE: int = Field(default=20 * 1024 * 1024)
    ALLOWED_EXTENSIONS: str = Field(default="pdf,png,jpg,jpeg")

    # ==========================
    # AI
    # ==========================
    GEMINI_API_KEY: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()