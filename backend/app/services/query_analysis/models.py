
from pydantic import BaseModel, Field

from app.common.constants import QueryIntent, QueryScope

class QueryAnalysis(BaseModel):
    intent: QueryIntent = QueryIntent.GENERAL
    scope: QueryScope = QueryScope.GLOBAL

    is_broad: bool = False
    requires_visual: bool = False

    page_numbers: list[int] = Field(
        default_factory=list
    )

    query_terms: list[str] = Field(
        default_factory=list
    )

    retrieval_top_k: int = 20