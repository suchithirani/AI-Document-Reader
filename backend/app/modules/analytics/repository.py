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

    async def get_dashboard(self, days: int = 7, owner_id: str | None = None):
        from datetime import datetime, timedelta, UTC
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
        match_stage = {
            "created_at": {"$gte": cutoff}
        }
        if owner_id:
            match_stage["user_id"] = owner_id

        pipeline = [
            {"$match": match_stage},
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
        days: int = 7,
        owner_id: str | None = None,
    ) -> int:
        from datetime import datetime, timedelta, UTC
        cutoff = datetime.now(UTC) - timedelta(days=days)
        filters = {
            "endpoint": endpoint,
            "created_at": {"$gte": cutoff}
        }
        if owner_id:
            filters["user_id"] = owner_id

        return await self.count(filters)

    async def get_daily_usage(self, days: int = 7, owner_id: str | None = None) -> list[dict]:
        from datetime import datetime, timedelta, UTC
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
        match_stage = {
            "created_at": {"$gte": cutoff}
        }
        if owner_id:
            match_stage["user_id"] = owner_id
            
        pipeline = [
            {"$match": match_stage},
            {
                "$project": {
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at",
                            "timezone": "Asia/Kolkata"
                        }
                    },
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 1,
                    "latency_ms": 1
                }
            },
            {
                "$group": {
                    "_id": "$date",
                    "prompt_tokens": {"$sum": "$prompt_tokens"},
                    "completion_tokens": {"$sum": "$completion_tokens"},
                    "total_tokens": {"$sum": "$total_tokens"},
                    "average_latency_ms": {"$avg": "$latency_ms"},
                    "requests_count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        cursor = await self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=100)
        return [
            {
                "date": r["_id"],
                "prompt_tokens": r["prompt_tokens"],
                "completion_tokens": r["completion_tokens"],
                "total_tokens": r["total_tokens"],
                "average_latency_ms": round(r["average_latency_ms"], 2) if r["average_latency_ms"] else 0,
                "requests_count": r["requests_count"]
            }
            for r in results
        ]

    async def get_model_splits(self, days: int = 7, owner_id: str | None = None) -> list[dict]:
        from datetime import datetime, timedelta, UTC
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
        match_stage = {
            "created_at": {"$gte": cutoff}
        }
        if owner_id:
            match_stage["user_id"] = owner_id
            
        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": {
                        "model": "$model",
                        "provider": "$provider"
                    },
                    "total_tokens": {"$sum": "$total_tokens"},
                    "requests_count": {"$sum": 1}
                }
            }
        ]
        
        cursor = await self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=50)
        return [
            {
                "model": r["_id"]["model"],
                "provider": r["_id"]["provider"],
                "total_tokens": r["total_tokens"],
                "requests_count": r["requests_count"]
            }
            for r in results
        ]