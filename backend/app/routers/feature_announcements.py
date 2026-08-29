from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database, get_optional_current_user
from app.models.feature_announcement import AnnouncementCategory
from app.models.user import User, UserRole
from app.schemas.feature_announcement import (
    FeatureAnnouncementCreate,
    FeatureAnnouncementListResponse,
    FeatureAnnouncementResponse,
    FeatureAnnouncementUpdate,
)
from app.services.feature_announcement_service import FeatureAnnouncementService

router = APIRouter(
    prefix="/feature-announcements",
    tags=["Feature Announcement Center"],
)


@router.get(
    "",
    response_model=FeatureAnnouncementListResponse,
    summary="List feature announcements",
    description="Get paginated list of announcements with optional search, category filters, and read status.",
)
def list_feature_announcements(
    category: AnnouncementCategory | None = Query(
        None, description="Filter by category"
    ),
    q: str | None = Query(
        None, description="Search term in title, summary, or content"
    ),
    is_featured: bool | None = Query(None, description="Filter by featured status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page"),
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
):
    user_id = current_user.id if current_user else None
    return FeatureAnnouncementService.list_announcements(
        db=db,
        user_id=user_id,
        category=category,
        q=q,
        is_featured=is_featured,
        page=page,
        limit=limit,
    )


@router.get(
    "/{announcement_id}",
    response_model=FeatureAnnouncementResponse,
    summary="Get announcement details",
)
def get_feature_announcement(
    announcement_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
):
    announcement = FeatureAnnouncementService.get_announcement(db, announcement_id)
    if not announcement or not announcement.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )

    res = FeatureAnnouncementResponse.model_validate(announcement)
    if current_user:
        # Mark as read automatically when viewed
        FeatureAnnouncementService.mark_as_read(db, current_user.id, announcement.id)
        res.is_read = True
    return res


@router.post(
    "/{announcement_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Mark announcement as read",
)
def mark_announcement_as_read(
    announcement_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    announcement = FeatureAnnouncementService.get_announcement(db, announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )
    FeatureAnnouncementService.mark_as_read(db, current_user.id, announcement_id)
    return {"message": "Announcement marked as read"}


@router.post(
    "/read-all",
    status_code=status.HTTP_200_OK,
    summary="Mark all announcements as read",
)
def mark_all_announcements_as_read(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    count = FeatureAnnouncementService.mark_all_as_read(db, current_user.id)
    return {"message": f"{count} announcements marked as read"}


# ==========================================================
# Admin Management Endpoints
# ==========================================================


@router.post(
    "/admin",
    response_model=FeatureAnnouncementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: Create feature announcement",
)
def create_feature_announcement_admin(
    payload: FeatureAnnouncementCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    announcement = FeatureAnnouncementService.create_announcement(
        db=db,
        admin_id=current_user.id,
        data=payload,
    )
    return FeatureAnnouncementResponse.model_validate(announcement)


@router.put(
    "/admin/{announcement_id}",
    response_model=FeatureAnnouncementResponse,
    summary="Admin: Update feature announcement",
)
def update_feature_announcement_admin(
    announcement_id: uuid.UUID,
    payload: FeatureAnnouncementUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    announcement = FeatureAnnouncementService.get_announcement(db, announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )
    updated = FeatureAnnouncementService.update_announcement(db, announcement, payload)
    return FeatureAnnouncementResponse.model_validate(updated)


@router.delete(
    "/admin/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Admin: Delete feature announcement",
)
def delete_feature_announcement_admin(
    announcement_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    announcement = FeatureAnnouncementService.get_announcement(db, announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )
    FeatureAnnouncementService.delete_announcement(db, announcement)
