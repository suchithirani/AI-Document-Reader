from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from backend.app.core.config import settings
from backend.app.core.logging import configure_logging, get_logger
from backend.app.database.connection import mongo_connection
from backend.app.modules.health.router import health_router

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Run startup and shutdown hooks for the application."""

    configure_logging(settings.log_level)
    logger.info("Starting application in %s mode", settings.environment)

    try:
        await mongo_connection.connect()
    except Exception as exc:  # pragma: no cover - startup should stay resilient
        logger.warning("MongoDB is unavailable: %s", exc)

    yield

    await mongo_connection.close()
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI Document Reader backend foundation",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.include_router(health_router, prefix=settings.api_prefix)
    return app


app = create_app()
