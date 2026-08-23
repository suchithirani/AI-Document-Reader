from app.core.config import settings


def test_settings_loaded_with_defaults() -> None:
    assert settings.APP_NAME == "AI Document Reader"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.ENVIRONMENT in {"development", "production", "testing"}
