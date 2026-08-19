from google import genai
from google.genai import types

from app.core.config import settings
from app.common.exceptions.ai import (
    AIAuthenticationException,
    AIResponseException,
)


class GeminiVision:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

    async def analyze_images(
        self,
        prompt: str,
        images: list[dict],
    ) -> str:

        if not images:
            return ""

        try:

            contents = [
                types.Part.from_text(
                    text=prompt
                )
            ]

            mime_types = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }

            for image in images:

                image_bytes = image.get(
                    "bytes"
                )

                if not image_bytes:
                    raise AIResponseException(
                        "Image bytes are empty."
                    )

                extension = (
                    image.get(
                        "extension",
                        "jpeg",
                    )
                    .lower()
                    .lstrip(".")
                )

                mime_type = mime_types.get(
                    extension
                )

                if not mime_type:
                    raise AIResponseException(
                        f"Unsupported image format: "
                        f"{extension}"
                    )

                contents.append(
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type,
                    )
                )

            response = (
                await self.client.aio.models.generate_content(
                    model=settings.VISION_MODEL,
                    contents=contents,
                )
            )

            answer = (
                response.text
                or ""
            ).strip()

            if not answer:
                raise AIResponseException(
                    "Empty vision response received "
                    "from Gemini."
                )

            return answer

        except AIResponseException:
            raise

        except Exception as exception:

            message = str(exception)
            lower = message.lower()

            if (
                "api key" in lower
                or "authentication" in lower
                or "unauthorized" in lower
                or "permission" in lower
            ):
                raise AIAuthenticationException(
                    message
                ) from exception

            raise AIResponseException(
                message
            ) from exception