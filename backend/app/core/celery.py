from celery import Celery
import app.workers.signal
from app.core.config import settings
from app.core.beat_schedule import BEAT_SCHEDULE

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
)

celery_app.conf.beat_schedule = BEAT_SCHEDULE
celery_app.conf.timezone = "Asia/Kolkata"