import asyncio
import logging

from app.core.celery import celery_app

from app.modules.auth.refresh_repository import (
    RefreshTokenRepository,
)
from app.services.storage.cleanup_service import (
    StorageCleanupService,
)
from app.core.config import (
    settings,
)
from app.modules.audit_logs.repository import AuditLogRepository
from app.workers.base import run_async_task, with_database

logger = logging.getLogger(__name__)


@celery_app.task(
    name="cleanup.refresh_tokens",
    auto_retry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def cleanup_refresh_tokens():

    run_async_task(
        with_database(
            cleanup_refresh_tokens_job,
        )
    )

async def cleanup_refresh_tokens_job(db):

    repository = RefreshTokenRepository(db)

    deleted = await repository.delete_expired_tokens()

    logger.info(
        "Deleted %d expired refresh tokens.",
        deleted,
    )

@celery_app.task(
    name="cleanup.temp_files",
    auto_retry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def cleanup_temp_files():

    service = StorageCleanupService()

    deleted = service.cleanup_directory(
        directory=settings.TEMP_DIRECTORY,
        retention_hours=settings.TEMP_FILE_RETENTION_HOURS,
    )

    logger.info(
        "Deleted %d temporary files.",
        deleted,
    )

@celery_app.task(
    name="cleanup.audit_logs",
    auto_retry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def cleanup_audit_logs():

    run_async_task(
        with_database(
            cleanup_audit_logs_job,
        )
    )

async def cleanup_audit_logs_job(db):

    repository = AuditLogRepository(db)

    deleted = await repository.delete_old_logs(
        settings.AUDIT_LOG_RETENTION_DAYS,
    )

    logger.info(
        "Deleted %d audit logs.",
        deleted,
    )