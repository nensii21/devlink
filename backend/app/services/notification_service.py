from __future__ import annotations

import uuid
from app.utils.time import utcnow

# pyrefly: ignore [missing-import]
from sqlalchemy import func, select

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
)
from app.core.cache import cached

class NotificationService:
    """
    Business logic for notifications.
    """

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
        channels=None,
        priority=None,
    ):
        if sender_id is not None and recipient_id == sender_id:
            return None

        from app.services.notifications import dispatcher
        from app.models.notification import NotificationType, NotificationPriority

        if not isinstance(type, NotificationType):
            try:
                type = NotificationType(type)
            except ValueError:
                pass

        if not priority:
            priority = NotificationPriority.NORMAL

        metadata_info = {
            "project_id": str(project_id) if project_id else None,
            "conversation_id": str(conversation_id) if conversation_id else None,
            "message_id": str(message_id) if message_id else None,
            "application_id": str(application_id) if application_id else None,
        }

        return dispatcher.dispatch(
            db=db,
            recipient_id=recipient_id,
            sender_id=sender_id,
            notification_type=type,
            title=title,
            message=message,
            channels=channels,
            priority=priority,
            metadata_info=metadata_info,
            action_url=action_url,
            image_url=image_url,
        )

    @staticmethod
    def create_notification(
        db: Session,
        recipient_id: uuid.UUID,
        sender_id: uuid.UUID | None,
        notification: NotificationCreate,
    ) -> Notification:
        db_notification = Notification(
            sender_id=sender_id,
            **notification.model_dump()
        )
        db.add(db_notification)
        db.flush()
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
    @cached(ttl=30, key_prefix="notifications:unread_count")
    def unread_count(
        db: Session,
        recipient_id: uuid.UUID,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.is_read.is_(False),
            )
        )

        return db.scalar(stmt) or 0

    @staticmethod
    def mark_as_read(
        db: Session,
        db_notification: Notification,
    ) -> Notification:

        db_notification.is_read = True
        db_notification.read_at = utcnow()

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
            notification.read_at = utcnow()

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

    @staticmethod
    def track_click(
        db: Session,
        db_notification: Notification,
    ) -> Notification:
        db_notification.clicked_at = utcnow()
        if not db_notification.is_read:
            db_notification.is_read = True
            db_notification.read_at = utcnow()
        db.flush()
        db.refresh(db_notification)
        return db_notification

    @staticmethod
    def track_delivered(
        db: Session,
        db_notification: Notification,
    ) -> Notification:
        db_notification.delivered_at = utcnow()
        from app.models.notification import NotificationStatus
        db_notification.status = NotificationStatus.SENT
        db.flush()
        db.refresh(db_notification)
        return db_notification

    @staticmethod
    def get_delivery_analytics(db: Session) -> dict:
        total_sent = db.scalar(
            select(func.count(Notification.id)).where(Notification.sent_at.isnot(None))
        ) or 0
        total_delivered = db.scalar(
            select(func.count(Notification.id)).where(Notification.delivered_at.isnot(None))
        ) or 0
        total_read = db.scalar(
            select(func.count(Notification.id)).where(Notification.read_at.isnot(None))
        ) or 0
        total_clicked = db.scalar(
            select(func.count(Notification.id)).where(Notification.clicked_at.isnot(None))
        ) or 0
        from app.models.notification import NotificationStatus
        total_failed = db.scalar(
            select(func.count(Notification.id)).where(Notification.status == NotificationStatus.FAILED)
        ) or 0

        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0.0
        read_rate = (total_read / total_delivered * 100) if total_delivered > 0 else 0.0
        click_rate = (total_clicked / total_read * 100) if total_read > 0 else 0.0

        return {
            "metrics": {
                "sent": total_sent,
                "delivered": total_delivered,
                "read": total_read,
                "clicked": total_clicked,
                "failed": total_failed,
            },
            "rates": {
                "delivery_rate_pct": round(delivery_rate, 2),
                "read_rate_pct": round(read_rate, 2),
                "click_rate_pct": round(click_rate, 2),
            },
        }

    @staticmethod
    def enqueue(
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
        from app.tasks.notification_tasks import send_notification_task

        payload = {
            "recipient_id": str(recipient_id) if recipient_id else None,
            "sender_id": str(sender_id) if sender_id else None,
            "type": type.value if hasattr(type, "value") else type,
            "title": title,
            "message": message,
            "action_url": action_url,
            "image_url": image_url,
            "project_id": str(project_id) if project_id else None,
            "conversation_id": str(conversation_id) if conversation_id else None,
            "message_id": str(message_id) if message_id else None,
            "application_id": str(application_id) if application_id else None,
        }

        send_notification_task.delay(payload)

    @staticmethod
    def get_preferences(
        db: Session,
        user_id: uuid.UUID,
    ):
        from app.models.notification import NotificationPreference
        pref = db.scalar(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        if not pref:
            now = utcnow()
            pref = NotificationPreference(
                id=uuid.uuid4(),
                user_id=user_id,
                email_enabled=True,
                websocket_enabled=True,
                database_enabled=True,
                messages=True,
                team_invitations=True,
                project_updates=True,
                mentions=True,
                system_announcements=True,
                email_messages=True,
                email_team_invitations=True,
                email_project_updates=True,
                email_mentions=True,
                email_system_announcements=True,
                invitations=True,
                role_changes=True,
                marketing_emails=False,
                system_alerts=True,
                updated_at=now,
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @staticmethod
    def update_preferences(
        db: Session,
        user_id: uuid.UUID,
        update_in: Any,
    ):
        from app.models.notification import NotificationPreference
        pref = NotificationService.get_preferences(db, user_id)
        data = update_in.model_dump(exclude_unset=True)

        for key, value in data.items():
            if hasattr(pref, key) and value is not None:
                setattr(pref, key, value)

        pref.updated_at = utcnow()
        db.add(pref)
        db.commit()
        db.refresh(pref)
        return pref
