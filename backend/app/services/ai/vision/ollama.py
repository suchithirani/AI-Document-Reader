import base64

import httpx

from app.common.exceptions.ai import (
    AIResponseException,
)
from app.core.config import settings
from app.services.ai.vision.provider import VisionProvider


class OllamaVision(VisionProvider):
    """Ollama implementation of the vision provider for local VLM."""

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_VISION_MODEL
        self.timeout = httpx.Timeout(120.0)

    async def analyze_images(
        self,
        prompt: str,
        images: list[dict],
    ) -> str:
        """
        Analyze document images using local Ollama.

        Args:
            prompt: Instructions for visual analysis.
            images: Images with their bytes and metadata.

        Returns:
            Ollama's visual analysis.
        """
        if not images:
            return ""

        try:
            base64_images = []

            for image in images:
                image_bytes = image.get("bytes")
                if not image_bytes:
                    raise AIResponseException("Image bytes are empty.")

                base64_encoded = base64.b64encode(image_bytes).decode("utf-8")
                base64_images.append(base64_encoded)

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "images": base64_images,
                    }
                ],
                "stream": False,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                if response.status_code != 200:
                    raise AIResponseException(
                        f"Ollama returned status {response.status_code}: {response.text}"
                    )

                data = response.json()

            answer = data.get("message", {}).get("content", "")

            if not answer:
                raise AIResponseException(
                    "Empty vision response received from Ollama."
                )

            return answer.strip()

        except AIResponseException:
            raise

        except Exception as exception:
            raise AIResponseException(
                f"Failed to communicate with Ollama Vision: {str(exception)}"
            ) from exception
