from app.core.celery import celery_app
from app.workers.database import get_worker_database
from app.modules.chat.title_service import (
    ChatTitleService,
)
from app.workers.base import run_async_task


@celery_app.task(
    name="chat.generate_title",
)
def generate_chat_title_task(
    session_id: str,
    question: str,
    answer: str,
):

    run_async_task(
        run_generate_title(
            session_id,
            question,
            answer,
        )
    )


async def run_generate_title(
    session_id: str,
    question: str,
    answer: str,
):

    _, db = await get_worker_database()


    service = ChatTitleService(
        db,
    )

    await service.generate_title(
        session_id,
        question,
        answer,
    )