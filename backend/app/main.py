from fastapi import FastAPI

from app.core.config import settings
from app.lifespan import lifespan
from app.modules.health.router import router as health_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(health_router)