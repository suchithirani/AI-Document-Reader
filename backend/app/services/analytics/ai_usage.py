
from app.core.config import settings
from app.modules.analytics.model import AIUsageLog
from app.modules.analytics.repository import (
    AnalyticsRepository,
)


class AIUsageService:

    def __init__(
        self,
        db,
    ):

        self.repository = AnalyticsRepository(
            db,
        )

    async def log(
        self,
        *,
        user_id: str | None,
        session_id: str | None,
        document_id: str | None,
        endpoint: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
    ):

        total_tokens = (
            prompt_tokens
            + completion_tokens
        )

        estimated_cost = self.calculate_cost(
            total_tokens,
        )

        usage = AIUsageLog(
            user_id=user_id,
            session_id=session_id,
            document_id=document_id,
            provider=settings.GENERATION_PROVIDER,
            model=settings.GENERATION_MODEL,
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            latency_ms=latency_ms,
        )

        await self.repository.create_ai_usage(
            usage.model_dump(
                by_alias=True,
                exclude_none=True,
            )
        )

    def calculate_cost(
        self,
        total_tokens: int,
    ) -> float:

        return round(
            total_tokens
            * 0.0000005,
            6,
        )
