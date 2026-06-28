from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
)


class NotificationService:
    """
    Business logic for notifications.
    """

    @staticmethod
    def create_notification(
        db: Session,
        recipient_id: uuid.UUID,
        sender_id: uuid.UUID | None,
        notification: NotificationCreate,
    ) -> Notification:

        db_notification = Notification(
            recipient_id=recipient_id,
            sender_id=sender_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            action_url=notification.action_url,
            image_url=notification.image_url,
            project_id=notification.project_id,
            conversation_id=notification.conversation_id,
            message_id=notification.message_id,
            application_id=notification.application_id,
        )

        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)

        return db_notification

    @staticmethod
    def get_notification(
        db: Session,
        notification_id: uuid.UUID,
    ) -> Notification | None:

        return db.get(Notification, notification_id)

    @staticmethod
    def list_notifications(
        db: Session,
        recipient_id: uuid.UUID,
    ) -> list[Notification]:

        stmt = (
            select(Notification)
            .where(Notification.recipient_id == recipient_id)
            .order_by(Notification.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_unread_notifications(
        db: Session,
        recipient_id: uuid.UUID,
    ) -> list[Notification]:

        stmt = (
            select(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.is_read.is_(False),
            )
            .order_by(Notification.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def unread_count(
        db: Session,
        recipient_id: uuid.UUID,
    ) -> int:

        stmt = (
            select(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.is_read.is_(False),
            )
        )

        return len(list(db.scalars(stmt)))

    @staticmethod
    def mark_as_read(
        db: Session,
        db_notification: Notification,
    ) -> Notification:

        db_notification.is_read = True
        db_notification.read_at = datetime.utcnow()

        db.commit()
        db.refresh(db_notification)

        return db_notification

    @staticmethod
    def mark_all_as_read(
        db: Session,
        recipient_id: uuid.UUID,
    ) -> None:

        stmt = (
            select(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.is_read.is_(False),
            )
        )

        notifications = list(db.scalars(stmt))

        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()

        db.commit()

    @staticmethod
    def update_notification(
        db: Session,
        db_notification: Notification,
        notification: NotificationUpdate,
    ) -> Notification:

        data = notification.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_notification, key, value)

        db.commit()
        db.refresh(db_notification)

        return db_notification

    @staticmethod
    def delete_notification(
        db: Session,
        db_notification: Notification,
    ) -> None:

        db.delete(db_notification)
        db.commit()