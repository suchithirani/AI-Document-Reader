import logging

from app.core.celery import celery_app
from app.core.config import (
    settings,
)
from app.modules.audit_logs.repository import AuditLogRepository
from app.modules.auth.refresh_repository import (
    RefreshTokenRepository,
)
from app.services.storage.cleanup_service import (
    StorageCleanupService,
)
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

@celery_app.task(
    name="cleanup.unreferenced_uploads",
    auto_retry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def cleanup_unreferenced_uploads():

    run_async_task(
        with_database(
            cleanup_unreferenced_uploads_job,
        )
    )

async def cleanup_unreferenced_uploads_job(db):
    import time
    from pathlib import Path

    from app.common.constants import CollectionName

    docs_col = db[CollectionName.DOCUMENTS.value]

    active_paths = set()
    cursor = docs_col.find({}, {"storage_path": 1})
    async for doc in cursor:
        path_str = doc.get("storage_path")
        if path_str:
            active_paths.add(Path(path_str).resolve())

    uploads_dir = Path("uploads").resolve()
    if not uploads_dir.exists():
        logger.info("Uploads directory does not exist. Skipping cleanup.")
        return

    cutoff = time.time() - (24 * 3600)
    deleted_count = 0

    for file_path in uploads_dir.rglob("*"):
        if not file_path.is_file():
            continue

        resolved_file = file_path.resolve()
        if resolved_file not in active_paths:
            if resolved_file.stat().st_mtime < cutoff:
                try:
                    resolved_file.unlink(missing_ok=True)
                    deleted_count += 1
                    logger.info("Deleted orphaned upload file: %s", resolved_file.name)
                except Exception as e:
                    logger.error("Failed to delete orphaned file %s: %s", resolved_file.name, e)

    logger.info("Deleted %d unreferenced/orphaned uploads.", deleted_count)
