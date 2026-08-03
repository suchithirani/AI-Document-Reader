from fastapi import APIRouter

from app.common.base_schema import ResponseSchema
from app.modules.health.service import health_service

health_router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@health_router.get(
    "",
    response_model=ResponseSchema,
)
async def health_check():
    health = await health_service.check_health()

    return ResponseSchema(
        message="Health check successful.",
        data=health,
    )