import asyncio
import time

from google import genai

from app.common.exceptions.ai import (
    AIAuthenticationException,
    AIResponseException,
)
from app.core.config import settings


class GeminiAIService:
    """Gemini provider for text generation."""

    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

    async def answer_question(
        self,
        prompt: str,
        model: str | None = None,
    ) -> dict:
        """
        Generate a text response using Gemini.

        Args:
            prompt: Prompt sent to the model.
            model: Optional specific model name.

        Returns:
            Generated answer and usage information.
        """
        try:
            start = time.perf_counter()

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model or settings.GENERATION_MODEL,
                contents=prompt,
            )

            latency = (
                time.perf_counter() - start
            ) * 1000

            usage = getattr(
                response,
                "usage_metadata",
                None,
            )

            answer = (
                response.text
                or ""
            ).strip()

            if not answer:
                raise AIResponseException(
                    "Empty response received from Gemini."
                )

            return {
                "answer": answer,
                "prompt_tokens": (
                    getattr(
                        usage,
                        "prompt_token_count",
                        0,
                    )
                    if usage
                    else 0
                ),
                "completion_tokens": (
                    getattr(
                        usage,
                        "candidates_token_count",
                        0,
                    )
                    if usage
                    else 0
                ),
                "total_tokens": (
                    getattr(
                        usage,
                        "total_token_count",
                        0,
                    )
                    if usage
                    else 0
                ),
                "latency_ms": round(
                    latency,
                    2,
                ),
            }

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

    async def answer_question_stream(
        self,
        prompt: str,
    ):
        """
        Generate a text response stream using Gemini.

        Args:
            prompt: Prompt sent to the model.

        Yields:
            Text chunks as they are generated.
        """
        try:
            response_stream = await self.client.aio.models.generate_content_stream(
                model=settings.GENERATION_MODEL,
                contents=prompt,
            )
            
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

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