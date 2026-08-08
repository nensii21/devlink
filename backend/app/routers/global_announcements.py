from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user, get_optional_current_user
from app.models.user import User, UserRole
from app.schemas.global_announcement import (
    GlobalAnnouncementCreate,
    GlobalAnnouncementResponse,
    GlobalAnnouncementUpdate,
)
from app.services.global_announcement_service import GlobalAnnouncementService

router = APIRouter(
    prefix="/announcements",
    tags=["Global Announcements"],
)


@router.get(
    "/active",
    response_model=list[GlobalAnnouncementResponse],
    summary="Get currently scheduled and active announcements",
)
def get_active_announcements(
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
):
    role = current_user.role if current_user else None
    return GlobalAnnouncementService.get_active_announcements_for_user(db, user_role=role)


@router.get(
    "/admin/all",
    response_model=list[GlobalAnnouncementResponse],
    summary="Admin API: List all global announcements",
)
def list_all_announcements_admin(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return GlobalAnnouncementService.list_all_announcements(db)


@router.post(
    "/admin",
    response_model=GlobalAnnouncementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin API: Create global announcement",
)
def create_announcement_admin(
    payload: GlobalAnnouncementCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return GlobalAnnouncementService.create_announcement(db, current_user.id, payload)


@router.put(
    "/admin/{announcement_id}",
    response_model=GlobalAnnouncementResponse,
    summary="Admin API: Update global announcement",
)
def update_announcement_admin(
    announcement_id: uuid.UUID,
    payload: GlobalAnnouncementUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    existing = GlobalAnnouncementService.get_announcement(db, announcement_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return GlobalAnnouncementService.update_announcement(db, existing, payload)


@router.delete(
    "/admin/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Admin API: Delete global announcement",
)
def delete_announcement_admin(
    announcement_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    existing = GlobalAnnouncementService.get_announcement(db, announcement_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")
    GlobalAnnouncementService.delete_announcement(db, existing)
