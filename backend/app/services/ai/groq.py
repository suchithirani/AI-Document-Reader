from groq import Groq
import time
from app.core.config import settings

from app.common.exceptions.ai import (
    AIResponseException,
)

class GroqAIService:

    def __init__(self):

        self.client = Groq(
            api_key=settings.GROQ_API_KEY,
        )

    async def answer_question(
        self,
        prompt: str,
    ) -> str:

        try:
            start = time.perf_counter()
            completion = (
                self.client.chat.completions.create(
                    model=settings.GENERATION_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                )
            )
            latency = (time.perf_counter() - start) * 1000
            answer = (
                completion
                .choices[0]
                .message
                .content
            )
            usage = completion.usage
            if not answer:

                raise AIResponseException(
                    "Empty response received from Groq."
                )

            return {
                "answer": answer.strip(),
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "latency_ms": round(latency, 2),
            }

        except AIResponseException:

            raise

        except Exception as exception:

            raise AIResponseException(
                str(exception)
            ) from exception