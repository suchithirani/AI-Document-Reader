from app.core.config import settings

from app.services.ai.gemini import GeminiAIService
from app.services.ai.groq import GroqAIService
from app.services.ai.vision_factory import VisionFactory


class AIService:

    def __init__(self):

        if settings.GENERATION_PROVIDER == "groq":
            self.provider = GroqAIService()
        else:
            self.provider = GeminiAIService()
            
        self.vision_engine = (
            VisionFactory.get_engine(
                settings.VISION_PROVIDER
            )
        )

    async def answer_question(
        self,
        prompt: str,
    ):
        return await self.provider.answer_question(
            prompt,
        )

    async def analyze_images(
        self,
        prompt: str,
        images: list[dict],
    ) -> str:

        return await self.vision_engine.analyze_images(
            prompt=prompt,
            images=images,
        )