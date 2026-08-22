import uuid
import logging
from typing import Any, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationPreference,
)
from app.services.notifications.channels.base import NotificationChannel
from app.services.notifications.channels.database_channel import DatabaseChannel
from app.services.notifications.channels.email_channel import EmailChannel
from app.services.notifications.channels.websocket_channel import WebSocketChannel
from app.services.notifications.preferences import (
    should_deliver,
    should_deliver_by_email,
)

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    def __init__(self):
        self.channels: dict[str, NotificationChannel] = {
            "database": DatabaseChannel(),
            "email": EmailChannel(),
            "websocket": WebSocketChannel(),
        }

    def _get_user_preferences(
        self, db: Session, user_id: uuid.UUID
    ) -> NotificationPreference:
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        prefs = db.scalars(stmt).first()
        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            db.add(prefs)
            db.flush()
        return prefs

    def _should_send_channel(
        self,
        channel_name: str,
        prefs: NotificationPreference,
        n_type: NotificationType,
    ) -> bool:
        """
        Whether this channel carries this notification.

        Two gates for email, not one. `email_enabled` is the master switch; the
        per-category `email_<category>` columns are the ones the settings page
        actually shows, and nothing read them before -- so "email me about
        mentions but not messages" was on or off for everything.
        """
        if channel_name == "database" and not prefs.database_enabled:
            return False
        if channel_name == "websocket" and not prefs.websocket_enabled:
            return False
        if channel_name == "email":
            if not prefs.email_enabled:
                return False
            if not should_deliver_by_email(n_type, prefs):
                return False
        return True

    def _should_send_type(
        self, n_type: NotificationType, prefs: NotificationPreference
    ) -> bool:
        """
        Whether the user wants this category at all.

        The mapping lives in `preferences.py` rather than in an `if` chain
        here: the chain's problem was that anything it did not name fell
        through to `True`, so nine of the fifteen types were undeniable and
        nothing made that visible.
        """
        return should_deliver(n_type, prefs)

    def dispatch(
        self,
        db: Session,
        recipient_id: uuid.UUID,
        sender_id: uuid.UUID | None,
        notification_type: NotificationType,
        title: str,
        message: str,
        channels: List[str] | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata_info: dict[str, Any] | None = None,
        action_url: str | None = None,
        image_url: str | None = None,
    ) -> List[Notification]:

        prefs = self._get_user_preferences(db, recipient_id)

        if not self._should_send_type(notification_type, prefs):
            logger.info(
                f"Notification {notification_type} disabled by user {recipient_id}"
            )
            return []

        if not channels:
            channels = ["database", "email", "websocket"]

        results = []
        for channel_name in channels:
            if not self._should_send_channel(channel_name, prefs, notification_type):
                continue

            channel = self.channels.get(channel_name)
            if not channel:
                logger.warning(f"Unknown notification channel: {channel_name}")
                continue

            try:
                notif = channel.send(
                    db=db,
                    recipient_id=recipient_id,
                    sender_id=sender_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    priority=priority,
                    metadata_info=metadata_info,
                    action_url=action_url,
                    image_url=image_url,
                )
                if notif:
                    results.append(notif)
            except Exception as e:
                logger.error(f"Error sending notification via {channel_name}: {e}")

        db.commit()
        return results


dispatcher = NotificationDispatcher()
