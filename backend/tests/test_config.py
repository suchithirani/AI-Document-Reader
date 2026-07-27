from backend.app.core.config import settings


def test_settings_loaded_with_defaults() -> None:
    assert settings.app_name == "AI Document Reader"
    assert settings.app_version == "0.1.0"
    assert settings.api_prefix == "/api/v1"
