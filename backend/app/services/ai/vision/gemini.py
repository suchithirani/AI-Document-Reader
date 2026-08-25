from google import genai
from google.genai import types

from app.common.exceptions.ai import (
    AIAuthenticationException,
    AIResponseException,
)
from app.core.config import settings
from app.services.ai.vision.provider import VisionProvider


class GeminiVision(VisionProvider):
    """Gemini implementation of the vision provider."""

    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

    async def analyze_images(
        self,
        prompt: str,
        images: list[dict],
    ) -> str:
        """
        Analyze document images using Gemini.

        Args:
            prompt: Instructions for visual analysis.
            images: Images with their bytes and metadata.

        Returns:
            Gemini's visual analysis.

        Raises:
            AIAuthenticationException: If Gemini authentication fails.
            AIResponseException: If image processing or Gemini response fails.
        """
        if not images:
            return ""

        try:
            contents = [
                types.Part.from_text(
                    text=prompt,
                )
            ]

            mime_types = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }

            for image in images:
                image_bytes = image.get("bytes")

                if not image_bytes:
                    raise AIResponseException(
                        "Image bytes are empty."
                    )

                extension = (
                    image.get("extension", "jpeg")
                    .lower()
                    .lstrip(".")
                )

                mime_type = mime_types.get(extension)

                if mime_type is None:
                    raise AIResponseException(
                        f"Unsupported image format: {extension}"
                    )

                contents.append(
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type,
                    )
                )

            response = (
                await self.client.aio.models.generate_content(
                    model=settings.GEMINI_VISION_MODEL,
                    contents=contents,
                )
            )

            answer = (response.text or "").strip()

            if not answer:
                raise AIResponseException(
                    "Empty vision response received from Gemini."
                )

            return answer

        except AIAuthenticationException:
            raise

        except AIResponseException:
            raise

        except Exception as exception:
            message = str(exception)
            lower_message = message.lower()

            if (
                "api key" in lower_message
                or "authentication" in lower_message
                or "unauthorized" in lower_message
                or "permission" in lower_message
            ):
                raise AIAuthenticationException(
                    message
                ) from exception

            raise AIResponseException(
                message
            ) from exception
