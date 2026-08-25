from app.core.celery import celery_app
from app.modules.chat.summary_service import (
    ChatSummaryService,
)
from app.workers.base import run_async_task
from app.workers.database import get_worker_database


@celery_app.task(
    name="chat.generate_summary",
)
def generate_summary_task(
    session_id: str,
):

    run_async_task(
        run_summary(
            session_id,
        )
    )


async def run_summary(
    session_id: str,
):

    client, db = await get_worker_database()

    try:

        service = ChatSummaryService(
            db,
        )

        await service.generate_summary(
            session_id,
        )

    finally:

        await client.close()
