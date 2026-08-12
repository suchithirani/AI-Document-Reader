import asyncio
import logging

from app.core.celery import celery_app
from app.services.email.schema import EmailRequest
from app.services.email.service import EmailService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="email.send",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 3,
    },
)
def send_email_task(
    email_data: dict,
):

    asyncio.run(
        run_send_email(
            email_data,
        )
    )


async def run_send_email(
    email_data: dict,
):

    email = EmailRequest.model_validate(
        email_data,
    )

    service = EmailService()

    await service.send(
        email,
    )

    logger.info(
        "Email sent successfully to %s",
        email.to_email,
    )