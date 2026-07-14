from __future__ import annotations

import uuid
from datetime import datetime

# pyrefly: ignore [missing-import]
from sqlalchemy import select

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
)

from app.schemas.notification import NotificationCreate


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

        # Check for existing unread duplicate notification
        stmt = select(Notification).where(
            Notification.recipient_id == recipient_id,
            Notification.type == notification.type,
            Notification.is_read.is_(False),
        )
        if sender_id is not None:
            stmt = stmt.where(Notification.sender_id == sender_id)
        if notification.project_id is not None:
            stmt = stmt.where(Notification.project_id == notification.project_id)
        if notification.conversation_id is not None:
            stmt = stmt.where(
                Notification.conversation_id == notification.conversation_id
            )
        if notification.application_id is not None:
            stmt = stmt.where(
                Notification.application_id == notification.application_id
            )

        existing = db.scalars(stmt).first()
        if existing:
            existing.message = notification.message
            existing.title = notification.title
            existing.created_at = datetime.utcnow()
            db.flush()
            db.refresh(existing)
            return existing

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
        db.flush()
        db.refresh(db_notification)

        return db_notification

    @staticmethod
    def notify(
        db: Session,
        recipient_id,
        sender_id,
        type,
        title,
        message,
        action_url=None,
        image_url=None,
        project_id=None,
        conversation_id=None,
        message_id=None,
        application_id=None,
    ):
        if sender_id is not None and recipient_id == sender_id:
            return None

        notification = NotificationCreate(
            recipient_id=recipient_id,
            type=type,
            title=title,
            message=message,
            action_url=action_url,
            image_url=image_url,
            project_id=project_id,
            conversation_id=conversation_id,
            message_id=message_id,
            application_id=application_id,
        )

        return NotificationService.create_notification(
            db=db,
            recipient_id=recipient_id,
            sender_id=sender_id,
            notification=notification,
        )

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

        stmt = select(Notification).where(
            Notification.recipient_id == recipient_id,
            Notification.is_read.is_(False),
        )

        return len(list(db.scalars(stmt)))

    @staticmethod
    def mark_as_read(
        db: Session,
        db_notification: Notification,
    ) -> Notification:

        db_notification.is_read = True
        db_notification.read_at = datetime.utcnow()

        db.flush()
        db.refresh(db_notification)

        return db_notification

    @staticmethod
    def mark_all_as_read(
        db: Session,
        recipient_id: uuid.UUID,
    ) -> None:

        stmt = select(Notification).where(
            Notification.recipient_id == recipient_id,
            Notification.is_read.is_(False),
        )

        notifications = list(db.scalars(stmt))

        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()

        db.flush()

    @staticmethod
    def update_notification(
        db: Session,
        db_notification: Notification,
        notification: NotificationUpdate,
    ) -> Notification:

        data = notification.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(db_notification, key, value)

        db.flush()
        db.refresh(db_notification)

        return db_notification

    @staticmethod
    def delete_notification(
        db: Session,
        db_notification: Notification,
    ) -> None:

        db.delete(db_notification)
        db.flush()
