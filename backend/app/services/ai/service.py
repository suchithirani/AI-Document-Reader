from app.core.config import settings

from app.services.ai.providers.gemini import (
    GeminiAIService,
)
from app.services.ai.providers.groq import (
    GroqAIService,
)
from app.services.ai.vision.gemini import (
    GeminiVision,
)
from app.services.ai.vision.groq import (
    GroqVision,
)
from app.services.ai.vision.router import (
    VisionRouter,
)


class AIService:

    def __init__(self) -> None:

        if settings.GENERATION_PROVIDER == "groq":
            self.provider = GroqAIService()
        else:
            self.provider = GeminiAIService()

        self.vision_router = VisionRouter(
            providers=[
                GeminiVision(),
                GroqVision(),
            ]
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

        return await self.vision_router.analyze_images(
            prompt=prompt,
            images=images,
        )