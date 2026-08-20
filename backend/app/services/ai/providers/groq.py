import asyncio
import time

from groq import Groq

from app.common.exceptions.ai import (
    AIAuthenticationException,
    AIResponseException,
)
from app.core.config import settings


class GroqAIService:
    """Groq provider for text generation."""

    def __init__(self) -> None:
        self.client = Groq(
            api_key=settings.GROQ_API_KEY,
            max_retries=0,
        )

    async def answer_question(
        self,
        prompt: str,
    ) -> dict:
        """
        Generate a text response using Groq.

        Args:
            prompt: Prompt sent to the model.

        Returns:
            Generated answer and usage information.
        """
        try:
            start = time.perf_counter()

            completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.GENERATION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            latency = (
                time.perf_counter() - start
            ) * 1000

            answer = (
                completion.choices[0].message.content
                or ""
            )

            usage = completion.usage

            if not answer:
                raise AIResponseException(
                    "Empty response received from Groq."
                )

            return {
                "answer": answer.strip(),
                "prompt_tokens": (
                    usage.prompt_tokens
                    if usage
                    else 0
                ),
                "completion_tokens": (
                    usage.completion_tokens
                    if usage
                    else 0
                ),
                "total_tokens": (
                    usage.total_tokens
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