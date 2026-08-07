from google import genai

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

            response = (
                self.client.models.generate_content(
                    model=settings.GENERATION_MODEL,
                    contents=prompt,
                )
            )

            if not response.text:

                raise AIResponseException(
                    "Empty response received from Gemini."
                )

            return response.text.strip()

        except AIResponseException:

            raise

        except Exception as exception:

            raise AIResponseException(
                str(exception)
            ) from exception