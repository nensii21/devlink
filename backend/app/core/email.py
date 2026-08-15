import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_FOLDER = Path(__file__).parent.parent / "templates" / "email"


class EmailService:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.SMTP_USERNAME,
            MAIL_PASSWORD=settings.SMTP_PASSWORD,
            MAIL_FROM=settings.EMAIL_FROM,
            MAIL_PORT=settings.SMTP_PORT,
            MAIL_SERVER=settings.SMTP_HOST or "localhost",
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True if settings.SMTP_PORT == 465 else False,
            USE_CREDENTIALS=bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD),
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=TEMPLATE_FOLDER,
        )
        self.fastmail = FastMail(self.conf)
        self.is_configured = bool(settings.SMTP_HOST)

    async def _send_email_async(
        self,
        subject: str,
        email_to: str,
        template_name: str,
        body_data: Dict[str, Any],
        background_tasks: BackgroundTasks | None = None,
    ) -> None:
        """
        Internal method to send emails either in background or immediately.
        """
        if not self.is_configured:
            logger.warning(
                f"Email not sent (SMTP not configured): {subject} to {email_to}"
            )
            return

        body_data["subject"] = subject  # inject subject to template context

        message = MessageSchema(
            subject=subject,
            recipients=[email_to],
            template_body=body_data,
            subtype=MessageType.html,
        )

        try:
            if background_tasks:
                background_tasks.add_task(
                    self.fastmail.send_message, message, template_name=template_name
                )
            else:
                await self.fastmail.send_message(message, template_name=template_name)
            logger.info(f"Email scheduled/sent to {email_to}: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {email_to}: {e}")

    def send_verification_email(
        self,
        email_to: str,
        username: str,
        verification_url: str,
        expire_hours: int,
        background_tasks: BackgroundTasks | None = None,
    ):
        from app.celery_app.tasks.email_tasks import send_verification_email_task

        send_verification_email_task.delay(
            email_to, username, verification_url, expire_hours
        )

    def send_password_reset_email(
        self,
        email_to: str,
        username: str,
        reset_url: str,
        expire_hours: int,
        background_tasks: BackgroundTasks | None = None,
    ):
        from app.celery_app.tasks.email_tasks import send_password_reset_email_task

        send_password_reset_email_task.delay(
            email_to, username, reset_url, expire_hours
        )

    def send_invitation_email(
        self,
        email_to: str,
        inviter_name: str,
        project_name: str,
        invitation_url: str,
        background_tasks: BackgroundTasks | None = None,
    ):
        from app.celery_app.tasks.email_tasks import send_invitation_email_task

        send_invitation_email_task.delay(
            email_to, inviter_name, project_name, invitation_url
        )

    def send_mention_email(
        self,
        email_to: str,
        username: str,
        mentioner_name: str,
        context_name: str,
        mention_text: str,
        context_url: str,
        background_tasks: BackgroundTasks | None = None,
    ):
        from app.celery_app.tasks.email_tasks import send_mention_email_task

        send_mention_email_task.delay(
            email_to, username, mentioner_name, context_name, mention_text, context_url
        )

    def send_app_update_email(
        self,
        email_to: str,
        username: str,
        update_title: str,
        update_content: str,
        action_url: str,
        background_tasks: BackgroundTasks | None = None,
    ):
        from app.celery_app.tasks.email_tasks import send_app_update_email_task

        send_app_update_email_task.delay(
            email_to, username, update_title, update_content, action_url
        )


email_service = EmailService()
