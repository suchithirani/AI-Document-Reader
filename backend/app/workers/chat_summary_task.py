import asyncio

from app.core.celery import celery_app
from app.workers.database import get_worker_database
from app.modules.chat.summary_service import (
    ChatSummaryService,
)


@celery_app.task(
    name="chat.generate_summary",
)
def generate_summary_task(
    session_id: str,
):

    asyncio.run(
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