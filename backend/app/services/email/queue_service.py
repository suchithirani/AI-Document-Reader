from app.services.email.templates import EmailTemplates
from app.workers.email_tasks import send_email_task


class EmailQueueService:

    def __init__(self) -> None:
        self.templates = EmailTemplates()

    async def send_welcome_email(
        self,
        username: str,
        email: str,
    ) -> None:

        request = self.templates.welcome(
            username=username,
            email=email,
        )

        send_email_task.delay(
            request.model_dump(
                mode="json",
            )
        )

    async def send_password_reset_email(
        self,
        email: str,
        otp: str,
    ) -> None:

        request = self.templates.password_reset(
            email=email,
            otp=otp,
        )

        send_email_task.delay(
            request.model_dump(
                mode="json",
            )
        )

    async def send_verification_email(
        self,
        email: str,
        otp: str,
    ) -> None:

        request = self.templates.email_verification(
            email=email,
            otp=otp,
        )

        send_email_task.delay(
            request.model_dump(
                mode="json",
            )
        )

    async def send_forgot_password_email(
        self,
        email: str,
        otp: str,
    ) -> None:

        request = self.templates.forgot_password(
            email=email,
            otp=otp,
        )

        send_email_task.delay(
            request.model_dump(
                mode="json",
            )
        )

    async def send_password_changed_email(
        self,
        email: str,
    ):

        request = self.templates.password_changed(
            email=email,
        )

        send_email_task.delay(
            request.model_dump(
                mode="json",
            )
        )

    async def send_document_processed_email(
        self,
        email: str,
        filename: str,
    ) -> None:

        request = self.templates.document_processed(
            email=email,
            filename=filename,
        )

        send_email_task.delay(
            request.model_dump(
                mode="json",
            )
        )

    async def send_document_failed_email(
        self,
        email: str,
        filename: str,
    ) -> None:

        request = self.templates.document_processing_failed(
            email=email,
            filename=filename,
        )

        send_email_task.delay(
            request.model_dump(
                mode="json",
            )
        )
