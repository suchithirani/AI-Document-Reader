from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import (
    close_mongodb_connection,
    connect_to_mongodb,
    get_database,
)
from app.core.logging import (
    logger,
    setup_logging,
)
from app.core.redis import (
    redis_client,
)
from app.database.indexes import (
    create_indexes,
)
from app.modules.request_logs.service import (
    RequestLogService,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    # ==========================================
    # Startup
    # ==========================================

    setup_logging()

    logger.info(
        "Starting AI Document Reader..."
    )

    # MongoDB
    await connect_to_mongodb()

    db = get_database()

    await create_indexes(db)

    # Redis
    await redis_client.ping()

    
    logger.info(
        "Redis connected successfully."
    )

    app.state.db = db

    app.state.redis_client = redis_client

    app.state.request_log_service = (
        RequestLogService(db)
    )

    logger.info(
        "Application started successfully."
    )

    yield

    # ==========================================
    # Shutdown
    # ==========================================

    logger.info(
        "Shutting down application..."
    )

    await close_mongodb_connection()

    await redis_client.close()

    logger.info(
        "Redis connection closed."
    )

    logger.info(
        "Application stopped."
    )