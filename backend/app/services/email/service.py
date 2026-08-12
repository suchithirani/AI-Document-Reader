from email.message import EmailMessage

import aiosmtplib

from app.common.exceptions.email import EmailException
from app.core.config import settings
from app.services.email.schema import EmailRequest

import logging

logger = logging.getLogger(__name__)
class EmailService:

    async def send(
        self,
        email: EmailRequest,
    ) -> None:

        message = EmailMessage()

        message["From"] = settings.SMTP_FROM
        message["To"] = email.to_email
        message["Subject"] = email.subject

        message.set_content(
            email.body,
        )

        try:

            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                start_tls=settings.SMTP_USE_TLS,
            )

        except Exception as exception:

            logger.exception(
                "Email sending failed."
            )

            raise EmailException(
                str(exception)
            ) from exception
                