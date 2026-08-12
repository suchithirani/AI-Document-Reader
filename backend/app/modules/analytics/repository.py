from app.common.constants import CollectionName
from app.modules.analytics.model import AIUsageLog
from app.repositories.base_repository import BaseRepository


class AnalyticsRepository(
    BaseRepository,
):

    def __init__(
        self,
        db,
    ):
        super().__init__(
            db[
                CollectionName.AI_USAGE_LOGS.value
            ]
        )

    async def create_ai_usage(
        self,
        usage: dict,
    ) -> AIUsageLog:

        created = await self.create(
            usage,
        )

        return AIUsageLog.model_validate(
            created,
        )

    async def get_dashboard(self):

        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_ai_requests": {
                        "$sum": 1,
                    },
                    "prompt_tokens": {
                        "$sum": "$prompt_tokens",
                    },
                    "completion_tokens": {
                        "$sum": "$completion_tokens",
                    },
                    "total_tokens": {
                        "$sum": "$total_tokens",
                    },
                    "estimated_cost": {
                        "$sum": "$estimated_cost",
                    },
                    "average_latency": {
                        "$avg": "$latency_ms",
                    },
                }
            }
        ]

        cursor = await self.collection.aggregate(
            pipeline,
        )

        result = await cursor.to_list(
            length=1,
        )

        return result[0] if result else None

    async def count_endpoint(
        self,
        endpoint: str,
    ) -> int:

        return await self.count(
            {
                "endpoint": endpoint,
            }
        )