from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.models.project import Project
from app.schemas.daily_digest import (
    DailyDigestResponse,
    DigestNotification,
    DigestProject,
)
from app.services.notification_service import NotificationService
from app.utils.time import ensure_utc, utcnow


class DailyDigestService:
    """
    Generates daily digest data.
    This service only prepares data.
    It does NOT send emails.
    """

    @staticmethod
    def generate_daily_digest(
        db: Session,
        recipient_id: uuid.UUID,
    ) -> DailyDigestResponse:
        since = utcnow() - timedelta(days=1)

        project_stmt = (
            select(Project)
            .where(Project.created_at >= since)
            .order_by(Project.created_at.desc())
        )

        new_projects = list(db.scalars(project_stmt))

        all_notifications = NotificationService.list_notifications(
            db=db,
            recipient_id=recipient_id,
        )

        # created_at comes back aware from Postgres but naive from SQLite, and
        # rows written before the naive/aware cleanup are naive either way.
        # Normalising here keeps this comparison from raising
        # `TypeError: can't compare offset-naive and offset-aware datetimes`,
        # which is what it did on Postgres for as long as `since` was naive.
        notifications = [
            notification
            for notification in all_notifications
            if ensure_utc(notification.created_at) >= since
        ]

        project_invitations: list[Notification] = []
        messages: list[Notification] = []
        other_notifications: list[Notification] = []

        for notification in notifications:
            if notification.type == NotificationType.PROJECT_INVITE:
                project_invitations.append(notification)
            elif notification.type == NotificationType.MESSAGE:
                messages.append(notification)
            else:
                other_notifications.append(notification)

        serialized_projects = [
            DigestProject(
                id=project.id,
                title=project.title,
                slug=project.slug,
                created_at=project.created_at,
            )
            for project in new_projects
        ]

        serialized_invitations = [
            DigestNotification(
                type=notification.type,
                title=notification.title,
                message=notification.message,
                action_url=notification.action_url,
                created_at=notification.created_at,
            )
            for notification in project_invitations
        ]

        serialized_messages = [
            DigestNotification(
                type=notification.type,
                title=notification.title,
                message=notification.message,
                action_url=notification.action_url,
                created_at=notification.created_at,
            )
            for notification in messages
        ]

        serialized_notifications = [
            DigestNotification(
                type=notification.type,
                title=notification.title,
                message=notification.message,
                action_url=notification.action_url,
                created_at=notification.created_at,
            )
            for notification in other_notifications
        ]

        return DailyDigestResponse(
            generated_at=utcnow(),
            new_projects=serialized_projects,
            project_invitations=serialized_invitations,
            messages=serialized_messages,
            notifications=serialized_notifications,
        )
