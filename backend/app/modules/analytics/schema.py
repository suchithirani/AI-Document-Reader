from app.common.base_schema import BaseSchema


class DailyUsageItem(BaseSchema):
    date: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    average_latency_ms: float
    requests_count: int

class ModelSplitItem(BaseSchema):
    model: str
    provider: str
    total_tokens: int
    requests_count: int

class DashboardResponse(BaseSchema):

    total_ai_requests: int

    total_prompt_tokens: int

    total_completion_tokens: int

    total_tokens: int

    total_estimated_cost: float

    average_latency_ms: float

    total_chat_requests: int

    total_title_requests: int

    total_summary_requests: int

    daily_usage: list[DailyUsageItem] = []
    model_splits: list[ModelSplitItem] = []
