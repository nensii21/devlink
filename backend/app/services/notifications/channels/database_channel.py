import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.notification import (
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationStatus,
    NotificationChannel as DBChannel,
)
from app.services.notifications.channels.base import NotificationChannel
from app.utils.time import utcnow


class DatabaseChannel(NotificationChannel):
    @property
    def name(self) -> str:
        return "database"

    def send(
        self,
        db: Session,
        recipient_id: uuid.UUID,
        sender_id: uuid.UUID | None,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority,
        metadata_info: dict[str, Any] | None = None,
        action_url: str | None = None,
        image_url: str | None = None,
    ) -> Notification:
        # Check for existing unread duplicate notification of the same type/recipient/sender
        stmt = select(Notification).where(
            Notification.recipient_id == recipient_id,
            Notification.type == notification_type,
            Notification.is_read.is_(False),
            Notification.channel == DBChannel.DATABASE,
        )
        if sender_id is not None:
            stmt = stmt.where(Notification.sender_id == sender_id)

        # We can also check if metadata_info matches, but for simplicity we'll just update existing if same type/sender
        existing = db.scalars(stmt).first()
        if existing:
            existing.message = message
            existing.title = title
            existing.created_at = utcnow()
            existing.metadata_info = metadata_info
            existing.action_url = action_url
            existing.image_url = image_url
            existing.priority = priority
            db.flush()
            db.refresh(existing)
            return existing

        db_notification = Notification(
            recipient_id=recipient_id,
            sender_id=sender_id,
            type=notification_type,
            channel=DBChannel.DATABASE,
            status=NotificationStatus.SENT,
            priority=priority,
            title=title,
            message=message,
            action_url=action_url,
            image_url=image_url,
            metadata_info=metadata_info,
            sent_at=utcnow(),
        )

        db.add(db_notification)
        db.flush()
        db.refresh(db_notification)

        return db_notification
