from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import (
    close_mongodb_connection,
    connect_to_mongodb,
    get_database,
)
from app.core.logging import logger, setup_logging
from app.modules.request_logs.service import RequestLogService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    """

    # Startup
    setup_logging()
    logger.info("Starting AI Document Reader...")

    await connect_to_mongodb()

    db = get_database()

    app.state.db = db
    app.state.request_log_service = RequestLogService(db)

    logger.info("Application started successfully.")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    await close_mongodb_connection()

    logger.info("Application stopped.")