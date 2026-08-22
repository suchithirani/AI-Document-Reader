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


from app.services.ai.providers.ollama import (
    OllamaAIService,
)

from app.services.ai.vision.ollama import (
    OllamaVision,
)

class AIService:

    def __init__(self) -> None:

        if settings.GENERATION_PROVIDER == "groq":
            self.provider = GroqAIService()
        elif settings.GENERATION_PROVIDER == "ollama":
            self.provider = OllamaAIService()
        else:
            self.provider = GeminiAIService()

        vision_providers = []
        if settings.VISION_PROVIDER == "ollama":
            vision_providers = [OllamaVision(), GeminiVision(), GroqVision()]
        elif settings.VISION_PROVIDER == "groq":
            vision_providers = [GroqVision(), GeminiVision(), OllamaVision()]
        else:
            vision_providers = [GeminiVision(), GroqVision(), OllamaVision()]

        self.vision_router = VisionRouter(
            providers=vision_providers
        )

    async def answer_question(
        self,
        prompt: str,
        model: str | None = None,
    ):
        import inspect
        sig = inspect.signature(self.provider.answer_question)
        if "model" in sig.parameters:
            return await self.provider.answer_question(
                prompt,
                model=model,
            )
        return await self.provider.answer_question(
            prompt,
        )

    async def answer_question_stream(
        self,
        prompt: str,
    ):
        async for chunk in self.provider.answer_question_stream(prompt):
            yield chunk

    async def analyze_images(
        self,
        prompt: str,
        images: list[dict],
    ) -> str:

        return await self.vision_router.analyze_images(
            prompt=prompt,
            images=images,
        )