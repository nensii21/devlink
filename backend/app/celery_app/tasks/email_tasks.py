import asyncio
import logging
from app.celery_app.celery import celery_app
from app.core.email import email_service

logger = logging.getLogger(__name__)


def run_async_email(coro):
    """Helper to run async email functions in synchronous celery task."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If running in an environment with an active loop (e.g. tests)
        import nest_asyncio

        nest_asyncio.apply()
    return asyncio.run(coro)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email_task(
    self, email_to: str, username: str, verification_url: str, expire_hours: int
):
    try:
        run_async_email(
            email_service._send_email_async(
                subject="Verify your DevLink email address",
                email_to=email_to,
                template_name="verification.html",
                body_data={
                    "username": username,
                    "verification_url": verification_url,
                    "expire_hours": expire_hours,
                },
            )
        )
    except Exception as exc:
        logger.error(f"Failed to send verification email to {email_to}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email_task(
    self, email_to: str, username: str, reset_url: str, expire_hours: int
):
    try:
        run_async_email(
            email_service._send_email_async(
                subject="Reset your DevLink password",
                email_to=email_to,
                template_name="password_reset.html",
                body_data={
                    "username": username,
                    "reset_url": reset_url,
                    "expire_hours": expire_hours,
                },
            )
        )
    except Exception as exc:
        logger.error(f"Failed to send password reset email to {email_to}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_invitation_email_task(
    self, email_to: str, inviter_name: str, project_name: str, invitation_url: str
):
    try:
        run_async_email(
            email_service._send_email_async(
                subject=f"You've been invited to join {project_name} on DevLink",
                email_to=email_to,
                template_name="invitation.html",
                body_data={
                    "inviter_name": inviter_name,
                    "project_name": project_name,
                    "invitation_url": invitation_url,
                },
            )
        )
    except Exception as exc:
        logger.error(f"Failed to send invitation email to {email_to}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_mention_email_task(
    self,
    email_to: str,
    username: str,
    mentioner_name: str,
    context_name: str,
    mention_text: str,
    context_url: str,
):
    try:
        run_async_email(
            email_service._send_email_async(
                subject=f"{mentioner_name} mentioned you on DevLink",
                email_to=email_to,
                template_name="mention.html",
                body_data={
                    "username": username,
                    "mentioner_name": mentioner_name,
                    "context_name": context_name,
                    "mention_text": mention_text,
                    "context_url": context_url,
                },
            )
        )
    except Exception as exc:
        logger.error(f"Failed to send mention email to {email_to}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_app_update_email_task(
    self,
    email_to: str,
    username: str,
    update_title: str,
    update_content: str,
    action_url: str,
):
    try:
        run_async_email(
            email_service._send_email_async(
                subject=f"DevLink Update: {update_title}",
                email_to=email_to,
                template_name="app_update.html",
                body_data={
                    "username": username,
                    "update_title": update_title,
                    "update_content": update_content,
                    "action_url": action_url,
                },
            )
        )
    except Exception as exc:
        logger.error(f"Failed to send app update email to {email_to}: {exc}")
        raise self.retry(exc=exc)
