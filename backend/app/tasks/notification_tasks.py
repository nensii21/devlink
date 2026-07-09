from __future__ import annotations

import logging
import uuid

from app.core.celery_app import celery_app
from app.database.session import SessionLocal
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def _to_uuid(value: str | None) -> uuid.UUID | None:
    return uuid.UUID(value) if value else None


@celery_app.task(
    name="notifications.send",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
)
def send_notification_task(self, payload: dict) -> str | None:
    db = SessionLocal()
    try:
        notification = NotificationService.notify(
            db,
            recipient_id=_to_uuid(payload["recipient_id"]),
            sender_id=_to_uuid(payload.get("sender_id")),
            type=NotificationType(payload["type"]),
            title=payload["title"],
            message=payload["message"],
            action_url=payload.get("action_url"),
            image_url=payload.get("image_url"),
            project_id=_to_uuid(payload.get("project_id")),
            conversation_id=_to_uuid(payload.get("conversation_id")),
            message_id=_to_uuid(payload.get("message_id")),
            application_id=_to_uuid(payload.get("application_id")),
        )
        return str(notification.id) if notification else None
    except Exception as exc:
        db.rollback()
        logger.exception("send_notification_task failed; retrying")
        raise self.retry(exc=exc)
    finally:
        db.close()