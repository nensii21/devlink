from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database.session import get_db
from app.models.notification import (
    Notification,
    NotificationStatus,
)
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/admin/notifications", tags=["Admin Notifications"])


@router.get("/stats")
def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get global notification delivery stats for the admin dashboard.
    Requires admin privileges.
    """
    if current_user.role != "admin":
        return {"detail": "Not authorized"}

    total = db.scalar(select(func.count(Notification.id))) or 0
    pending = (
        db.scalar(
            select(func.count(Notification.id)).where(
                Notification.status == NotificationStatus.PENDING
            )
        )
        or 0
    )
    failed = (
        db.scalar(
            select(func.count(Notification.id)).where(
                Notification.status == NotificationStatus.FAILED
            )
        )
        or 0
    )
    sent = (
        db.scalar(
            select(func.count(Notification.id)).where(
                Notification.status == NotificationStatus.SENT
            )
        )
        or 0
    )
    read = (
        db.scalar(
            select(func.count(Notification.id)).where(
                Notification.status == NotificationStatus.READ
            )
        )
        or 0
    )

    return {
        "total": total,
        "pending": pending,
        "failed": failed,
        "sent": sent,
        "read": read,
    }


@router.get("/failed")
def get_failed_notifications(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a list of failed notifications for retry.
    """
    if current_user.role != "admin":
        return {"detail": "Not authorized"}

    stmt = (
        select(Notification)
        .where(Notification.status == NotificationStatus.FAILED)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    notifications = list(db.scalars(stmt))
    return notifications


@router.post("/{notification_id}/retry")
def retry_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retry a specific failed notification.
    """
    if current_user.role != "admin":
        return {"detail": "Not authorized"}

    notification = db.get(Notification, notification_id)
    if not notification:
        return {"detail": "Notification not found"}

    notification.status = NotificationStatus.PENDING
    db.commit()

    # Re-enqueue the task
    from app.services.notification_service import NotificationService

    NotificationService.enqueue(
        db,
        recipient_id=notification.recipient_id,
        sender_id=notification.sender_id,
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

    return {"status": "retrying"}
