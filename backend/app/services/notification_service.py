from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
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
    def notify(
        db: Session,
        *,
        recipient_id: uuid.UUID,
        sender_id: uuid.UUID | None,
        type: NotificationType,
        title: str,
        message: str,
        action_url: str | None = None,
        image_url: str | None = None,
        project_id: uuid.UUID | None = None,
        conversation_id: uuid.UUID | None = None,
        message_id: uuid.UUID | None = None,
        application_id: uuid.UUID | None = None,
    ) -> Notification | None:
        if sender_id is not None and recipient_id == sender_id:
            return None

        db_notification = Notification(
            recipient_id=recipient_id,
            sender_id=sender_id,
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

        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)

        return db_notification

    @staticmethod
    def enqueue(
        db: Session,
        *,
        recipient_id: uuid.UUID,
        sender_id: uuid.UUID | None,
        type: NotificationType,
        title: str,
        message: str,
        action_url: str | None = None,
        image_url: str | None = None,
        project_id: uuid.UUID | None = None,
        conversation_id: uuid.UUID | None = None,
        message_id: uuid.UUID | None = None,
        application_id: uuid.UUID | None = None,
    ) -> None:
        if sender_id is not None and recipient_id == sender_id:
            return

        def _s(v: uuid.UUID | None) -> str | None:
            return str(v) if v is not None else None

        payload = {
            "recipient_id": _s(recipient_id),
            "sender_id": _s(sender_id),
            "type": type.value,
            "title": title,
            "message": message,
            "action_url": action_url,
            "image_url": image_url,
            "project_id": _s(project_id),
            "conversation_id": _s(conversation_id),
            "message_id": _s(message_id),
            "application_id": _s(application_id),
        }

        from app.tasks.notification_tasks import send_notification_task

        try:
            send_notification_task.delay(payload)
        except Exception:
            NotificationService.notify(
                db,
                recipient_id=recipient_id,
                sender_id=sender_id,
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

        db.commit()
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
