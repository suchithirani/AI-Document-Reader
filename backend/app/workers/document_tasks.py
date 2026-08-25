
from app.core.celery import celery_app
from app.modules.documents.document_process_service import (
    DocumentProcessingService,
)
from app.workers.base import run_async_task
from app.workers.database import get_worker_database


@celery_app.task(
    name="documents.process_batch",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={
        "max_retries": 5,
    },
)
def process_documents_batch_task(
    owner_id: str,
    document_ids: list[str],
):

    run_async_task(
        run_documents_processing(
            owner_id=owner_id,
            document_ids=document_ids,
        )
    )


async def run_documents_processing(
    owner_id: str,
    document_ids: list[str],
):

    _, db = await get_worker_database()

    service = DocumentProcessingService(
        db,
    )

    await service.process_documents(
        owner_id=owner_id,
        document_ids=document_ids,
    )
