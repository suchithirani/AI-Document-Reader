from app.services.ai.gemini_vision import (
    GeminiVision,
)


class VisionFactory:

    @staticmethod
    def get_engine(
        provider: str,
    ):

        provider = provider.lower()

        if provider == "gemini":
            return GeminiVision()

        raise ValueError(
            f"Unsupported vision provider: {provider}"
        )