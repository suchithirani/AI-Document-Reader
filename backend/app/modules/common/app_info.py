from pathlib import Path

from backend.app.core.config import settings


class AppInfo:
    """Expose simple application metadata for startup or diagnostics."""

    @classmethod
    def get_summary(cls) -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }
