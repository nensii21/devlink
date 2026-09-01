from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)
from app.services.notification_service import NotificationService
from app.core.cache import cache_manager, cached

router = APIRouter(
    tags=["Notifications"],
)


@router.post(
    "/",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    result = NotificationService.create_notification(
        db=db,
        recipient_id=notification.recipient_id,
        sender_id=current_user.id,
        notification=notification,
    )
    cache_manager.delete_pattern(f"notifs_count:*{notification.recipient_id}*")
    return result


from typing import Optional
from fastapi import Query

@router.get(
    "/",
    response_model=list[NotificationResponse],
)
def list_notifications(
    type_filter: Optional[str] = Query(None, alias="type"),
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return NotificationService.list_notifications(
        db,
        current_user.id,
        type_filter=type_filter,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/unread",
    response_model=list[NotificationResponse],
)
def unread_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return NotificationService.list_unread_notifications(
        db,
        current_user.id,
    )


@router.get(
    "/unread/count",
)
@cached(ttl=600, key_prefix="notifs_count")
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return {
        "count": NotificationService.unread_count(
            db,
            current_user.id,
        )
    }


@router.patch(
    "/read-all",
)
def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    NotificationService.mark_all_as_read(
        db,
        current_user.id,
    )
    cache_manager.delete_pattern(f"notifs_count:*{current_user.id}*")

    return {
        "message": "All notifications marked as read",
    }


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def get_notification(
    notification_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    notification = NotificationService.get_notification(
        db,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    return notification


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_as_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    notification = NotificationService.get_notification(
        db,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    result = NotificationService.mark_as_read(
        db,
        notification,
    )
    cache_manager.delete_pattern(f"notifs_count:*{notification.recipient_id}*")
    return result


@router.put(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def update_notification(
    notification_id: uuid.UUID,
    notification: NotificationUpdate,
    db: Session = Depends(get_database),
):

    db_notification = NotificationService.get_notification(
        db,
        notification_id,
    )

    if db_notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    result = NotificationService.update_notification(
        db,
        db_notification,
        notification,
    )
    cache_manager.delete_pattern(f"notifs_count:*{db_notification.recipient_id}*")
    return result


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    notification = NotificationService.get_notification(
        db,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    if notification.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this notification",
        )

    NotificationService.delete_notification(
        db,
        notification,
    )
    cache_manager.delete_pattern(f"notifs_count:*{notification.recipient_id}*")


from app.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)


@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Get Notification Preferences",
    description="Retrieve current user's notification preferences across messages, team invitations, project updates, mentions, system announcements, and email settings.",
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
) -> NotificationPreferenceResponse:
    pref = NotificationService.get_preferences(db, user_id=current_user.id)
    return NotificationPreferenceResponse.model_validate(pref)


@router.put(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Update Notification Preferences (PUT)",
    description="Update current user's notification settings for all channels and categories.",
)
@router.patch(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Update Notification Preferences (PATCH)",
    description="Partially update current user's notification settings.",
)
def update_preferences(
    prefs: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
) -> NotificationPreferenceResponse:
    pref = NotificationService.update_preferences(
        db, user_id=current_user.id, update_in=prefs
    )
    return NotificationPreferenceResponse.model_validate(pref)


@router.post(
    "/{notification_id}/click",
    response_model=NotificationResponse,
    summary="Track notification click interaction",
)
def track_click(
    notification_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    notification = NotificationService.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationService.track_click(db, notification)


@router.post(
    "/{notification_id}/delivered",
    response_model=NotificationResponse,
    summary="Track notification delivery status",
)
def track_delivered(
    notification_id: uuid.UUID,
    db: Session = Depends(get_database),
):
    notification = NotificationService.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationService.track_delivered(db, notification)


@router.get(
    "/analytics/delivery",
    summary="Get notification delivery and interaction analytics dashboard responses",
)
def get_delivery_analytics(
    db: Session = Depends(get_database),
):
    return NotificationService.get_delivery_analytics(db)
