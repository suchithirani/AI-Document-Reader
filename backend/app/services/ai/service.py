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
            self.fallback_providers = [GeminiAIService(), OllamaAIService()]
        elif settings.GENERATION_PROVIDER == "ollama":
            self.provider = OllamaAIService()
            self.fallback_providers = [GeminiAIService(), GroqAIService()]
        else:
            self.provider = GeminiAIService()
            self.fallback_providers = [GroqAIService(), OllamaAIService()]

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
        import logging
        logger = logging.getLogger(__name__)
        
        providers = [self.provider] + self.fallback_providers
        last_exc = None
        
        for prov in providers:
            try:
                import inspect
                sig = inspect.signature(prov.answer_question)
                if "model" in sig.parameters:
                    return await prov.answer_question(
                        prompt,
                        model=model,
                    )
                return await prov.answer_question(
                    prompt,
                )
            except Exception as e:
                logger.warning(
                    "AIService provider %s failed: %s. Trying next provider...",
                    prov.__class__.__name__,
                    e
                )
                last_exc = e
                continue
                
        raise last_exc

    async def answer_question_stream(
        self,
        prompt: str,
    ):
        import logging
        logger = logging.getLogger(__name__)
        
        providers = [self.provider] + self.fallback_providers
        last_exc = None
        
        for prov in providers:
            try:
                gen = prov.answer_question_stream(prompt)
                # Fetch first chunk to verify it initializes successfully (catches 429)
                first_chunk = await gen.__anext__()
                yield first_chunk
                
                async for chunk in gen:
                    yield chunk
                return
            except StopAsyncIteration:
                return
            except Exception as e:
                logger.warning(
                    "AIService stream provider %s failed: %s. Trying fallback stream...",
                    prov.__class__.__name__,
                    e
                )
                last_exc = e
                continue
                
        raise last_exc

    async def analyze_images(
        self,
        prompt: str,
        images: list[dict],
    ) -> str:

        return await self.vision_router.analyze_images(
            prompt=prompt,
            images=images,
        )