from app.common.base_schema import BaseSchema


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