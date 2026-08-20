import asyncio
import base64

from groq import Groq

from app.common.exceptions.ai import (
    AIAuthenticationException,
    AIResponseException,
)
from app.core.config import settings
from app.services.ai.vision.provider import VisionProvider


class GroqVision(VisionProvider):
    """Groq provider for visual analysis."""

    MAX_COMPLETION_TOKENS = 1200

    def __init__(self) -> None:
        self.client = Groq(
            api_key=settings.GROQ_API_KEY,
            max_retries=0,
        )

    async def analyze_images(
        self,
        prompt: str,
        images: list[dict],
    ) -> str:
        """
        Analyze images using Groq vision.

        Args:
            prompt: Visual analysis prompt.
            images: Images to analyze.

        Returns:
            Visual analysis response.
        """
        if not images:
            return ""

        content = self._build_vision_content(
            prompt=prompt,
            images=images,
        )

        try:
            completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.GROQ_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
                max_completion_tokens=(
                    self.MAX_COMPLETION_TOKENS
                ),
                reasoning_effort="none",
                reasoning_format="hidden",
            )

            answer = (
                completion.choices[0]
                .message.content
                or ""
            )

            answer = self._clean_response(
                answer
            )

            if not answer:
                raise AIResponseException(
                    "Empty vision response received from Groq."
                )

            return answer

        except AIAuthenticationException:
            raise

        except AIResponseException:
            raise

        except Exception as exception:

            message = str(exception)
            lower = message.lower()

            if (
                "invalid api key" in lower
                or "expired_api_key" in lower
                or "unauthorized" in lower
                or "authentication" in lower
            ):
                raise AIAuthenticationException(
                    message
                ) from exception

            raise AIResponseException(
                message
            ) from exception

    @staticmethod
    def _build_vision_content(
        prompt: str,
        images: list[dict],
    ) -> list[dict]:

        content = [
            {
                "type": "text",
                "text": prompt,
            }
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

            if mime_type is None:
                raise AIResponseException(
                    f"Unsupported image format: {extension}"
                )

            encoded_image = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            data_url = (
                f"data:{mime_type};base64,"
                f"{encoded_image}"
            )

            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": data_url,
                    },
                }
            )

        return content

    @staticmethod
    def _clean_response(
        response: str,
    ) -> str:

        if not response:
            return ""

        response = response.strip()

        while True:

            lower = response.lower()

            start = lower.find(
                "<think>"
            )

            if start == -1:
                break

            end = lower.find(
                "</think>",
                start,
            )

            if end == -1:
                response = response[:start]
                break

            end += len("</think>")

            response = (
                response[:start]
                + response[end:]
            )

        return response.replace(
            "</think>",
            "",
        ).strip()