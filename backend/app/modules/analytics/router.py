from fastapi import APIRouter, Depends

from app.common.response import success_response
from app.dependencies.auth import get_current_user
from app.dependencies.service import (
    get_analytics_service,
)
from app.modules.analytics.service import (
    AnalyticsService,
)
from app.modules.auth.model import User

analytics_router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@analytics_router.get(
    "/dashboard",
)
async def dashboard(
    days: int = 7,
    current_user: User = Depends(
        get_current_user,
    ),
    service: AnalyticsService = Depends(
        get_analytics_service,
    ),
):

    result = await service.dashboard(
        days=days,
        owner_id=current_user.id
    )

    return success_response(
        message="Analytics fetched successfully.",
        data=result,
    )
