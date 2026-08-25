from app.modules.analytics.repository import (
    AnalyticsRepository,
)
from app.modules.analytics.schema import (
    DashboardResponse,
)


class AnalyticsService:

    def __init__(
        self,
        db,
    ):

        self.repository = AnalyticsRepository(
            db,
        )

    async def dashboard(
        self,
        days: int = 7,
        owner_id: str | None = None,
    ):
        stats = await self.repository.get_dashboard(days, owner_id)

        if stats is None:
            stats = {}

        daily_usage = await self.repository.get_daily_usage(days, owner_id)
        model_splits = await self.repository.get_model_splits(days, owner_id)

        return DashboardResponse(
            total_ai_requests=stats.get(
                "total_ai_requests",
                0,
            ),
            total_prompt_tokens=stats.get(
                "prompt_tokens",
                0,
            ),
            total_completion_tokens=stats.get(
                "completion_tokens",
                0,
            ),
            total_tokens=stats.get(
                "total_tokens",
                0,
            ),
            total_estimated_cost=round(
                stats.get(
                    "estimated_cost",
                    0,
                ),
                6,
            ),
            average_latency_ms=round(
                stats.get(
                    "average_latency",
                    0,
                ),
                2,
            ),
            total_chat_requests=await self.repository.count_endpoint(
                "chat",
                days,
                owner_id
            ),
            total_title_requests=await self.repository.count_endpoint(
                "title_generation",
                days,
                owner_id
            ),
            total_summary_requests=await self.repository.count_endpoint(
                "conversation_summary",
                days,
                owner_id
            ),
            daily_usage=daily_usage,
            model_splits=model_splits,
        )
