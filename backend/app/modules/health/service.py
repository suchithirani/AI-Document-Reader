from app.core.config import settings
from app.modules.health.schema import HealthResponse


class HealthService:
    """
    Business logic for health endpoints.
    """

    @staticmethod
    async def check_health() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            application=settings.APP_NAME,
            version=settings.APP_VERSION,
        )


health_service = HealthService()
