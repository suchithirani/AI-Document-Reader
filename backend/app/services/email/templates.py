from app.services.email.schema import EmailRequest


class EmailTemplates:

    @staticmethod
    def welcome(
        username: str,
        email: str,
    ) -> EmailRequest:

        return EmailRequest(
            to_email=email,
            subject="Welcome to AI Document Reader",
            body=f"""
Hello {username},

Welcome to AI Document Reader.

Your account has been created successfully.

Thanks,
AI Document Reader Team
""",
        )

    @staticmethod
    def password_reset(
        reset_link: str,
    ) -> tuple[str, str]:

        subject = "Reset Your Password"

        body = f"""
Hello,

We received a request to reset your password.

Reset your password using the link below:

{reset_link}

If you didn't request this, you can safely ignore this email.

Regards,
AI Document Reader Team
"""

        return subject, body

    @staticmethod
    def email_verification(
        email: str,
        otp: str,
    ) -> EmailRequest:

        return EmailRequest(
            to_email=email,
            subject="Verify Your Email",
            body=f"""
    Hello,

    Your email verification OTP is:

    {otp}

    This OTP is valid for 5 minutes.

    If you didn't request this, please ignore this email.

    Regards,
    AI Document Reader Team
    """,
        )

    @staticmethod
    def forgot_password(
        email: str,
        otp: str,
    ) -> EmailRequest:

        return EmailRequest(
            to_email=email,
            subject="Reset Your Password",
            body=f"""
    Hello,

    Your password reset OTP is:

    {otp}

    This OTP will expire in 5 minutes.

    If you didn't request this, please ignore this email.

    Regards,
    AI Document Reader Team
    """,
        )

    @staticmethod
    def password_changed(
        email: str,
    ) -> EmailRequest:

        return EmailRequest(
            to_email=email,
            subject="Password Changed Successfully",
            body="""
    Hello,

    Your password has been changed successfully.

    If you did not perform this action, please contact support immediately.

    Regards,
    AI Document Reader Team
    """,
        )

    @staticmethod
    def document_processed(
        filename: str,
    ) -> tuple[str, str]:

        subject = "Document Processing Completed"

        body = f"""
Hello,

Your document

{filename}

has been processed successfully.

You can now start chatting with it.

Regards,
AI Document Reader Team
"""

        return subject, body

    @staticmethod
    def document_processing_failed(
        filename: str,
    ) -> tuple[str, str]:

        subject = "Document Processing Failed"

        body = f"""
Hello,

Unfortunately,

{filename}

could not be processed.

Please upload the document again.

Regards,
AI Document Reader Team
"""

        return subject, body