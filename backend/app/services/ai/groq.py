from groq import Groq

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

            answer = (
                completion
                .choices[0]
                .message
                .content
            )

            if not answer:

                raise AIResponseException(
                    "Empty response received from Groq."
                )

            return answer.strip()

        except AIResponseException:

            raise

        except Exception as exception:

            raise AIResponseException(
                str(exception)
            ) from exception