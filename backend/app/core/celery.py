from celery import Celery

from app.core.beat_schedule import BEAT_SCHEDULE
from app.core.config import settings

celery_app = Celery(
    "ai_document_reader",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.imports = (
    "app.workers.document_tasks",
    "app.workers.cleanup_tasks",
    "app.workers.email_tasks",
    "app.workers.chat_tasks",
    "app.workers.chat_summary_task",
    "app.workers.ai_tasks",
)
celery_app.conf.beat_schedule = BEAT_SCHEDULE
celery_app.conf.timezone = "Asia/Kolkata"
