from app.core.config import settings

from app.services.ai.gemini import GeminiAIService
from app.services.ai.groq import GroqAIService
class AIService:

    def __init__(self):

        if settings.GENERATION_PROVIDER == "groq":
            self.provider = GroqAIService()
        else:
            self.provider = GeminiAIService()

    async def answer_question(
        self,
        prompt: str,
    ):
        return await self.provider.answer_question(
            prompt,
        )