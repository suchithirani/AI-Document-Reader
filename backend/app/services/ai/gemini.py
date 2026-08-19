import asyncio

from google import genai
import time
from app.core.config import settings
from app.common.exceptions.ai import (
    AIResponseException,
)

class GeminiAIService:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

    async def answer_question(
        self,
        prompt: str,
    ) -> str:

        try:
            start = time.perf_counter()
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=settings.VISION_MODEL,
                contents=prompt,
            )
            latency = (time.perf_counter() - start) * 1000
            usage = getattr(response, "usage", None)
            if not response.text:

                raise AIResponseException(
                    "Empty response received from Gemini."
                )

            return {
                "answer": response.text.strip(),
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.candidates_token_count if usage else 0,
                "total_tokens": usage.total_token_count if usage else 0,
                "latency_ms": round(latency, 2),
            }

        except AIResponseException:

            raise

        except Exception as exception:

            raise AIResponseException(
                str(exception)
            ) from exception