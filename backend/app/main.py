from fastapi import FastAPI

from app.common.exceptions.auth import register_exception_handlers
from app.core.config import settings
from app.lifespan import lifespan

from app.middleware.cors import configure_cors
from app.middleware.logging import logging_middleware
from app.middleware.process_time import process_time_middleware
from app.middleware.request_id import request_id_middleware
from app.modules.documents.router import (
    document_router,
)
from app.modules.search.router import (
    search_router,
)
from app.modules.chat.router import (
    chat_router,
)
from app.modules.auth.router import auth_router
from app.modules.health.router import health_router
from app.modules.analytics.router import analytics_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Middleware
app.middleware("http")(request_id_middleware)
app.middleware("http")(process_time_middleware)
app.middleware("http")(logging_middleware)

configure_cors(app)

# Exception Handlers
register_exception_handlers(app)

# Routers
app.include_router(
    health_router,
    prefix="/api/v1",
)

app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    document_router,
    prefix="/api/v1",
)
app.include_router(
    search_router,
    prefix="/api/v1",
)

app.include_router(
    chat_router,
    prefix="/api/v1",
)

app.include_router(
    analytics_router,
    prefix="/api/v1",
)