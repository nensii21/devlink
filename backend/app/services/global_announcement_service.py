from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.models.global_announcement import GlobalAnnouncement, TargetAudience
from app.schemas.global_announcement import GlobalAnnouncementCreate, GlobalAnnouncementUpdate


class GlobalAnnouncementService:
    """
    Business logic for Global Announcement management.
    """

    @staticmethod
    def create_announcement(
        db: Session, admin_id: uuid.UUID, data: GlobalAnnouncementCreate
    ) -> GlobalAnnouncement:
        announcement = GlobalAnnouncement(
            created_by_id=admin_id,
            title=data.title,
            content=data.content,
            severity=data.severity,
            target_audience=data.target_audience,
            start_date=data.start_date,
            end_date=data.end_date,
            is_active=data.is_active,
        )
        db.add(announcement)
        db.flush()
        db.refresh(announcement)
        return announcement

    @staticmethod
    def get_announcement(db: Session, announcement_id: uuid.UUID) -> GlobalAnnouncement | None:
        return db.get(GlobalAnnouncement, announcement_id)

    @staticmethod
    def list_all_announcements(db: Session) -> list[GlobalAnnouncement]:
        stmt = select(GlobalAnnouncement).order_by(GlobalAnnouncement.created_at.desc())
        return list(db.scalars(stmt))

    @staticmethod
    def get_active_announcements_for_user(
        db: Session, user_role: str | None = None
    ) -> list[GlobalAnnouncement]:
        now = datetime.utcnow()
        stmt = select(GlobalAnnouncement).where(
            GlobalAnnouncement.is_active == True,
            GlobalAnnouncement.start_date <= now,
            or_(
                GlobalAnnouncement.end_date.is_(None),
                GlobalAnnouncement.end_date >= now,
            ),
        )

        if user_role == "admin":
            stmt = stmt.where(
                or_(
                    GlobalAnnouncement.target_audience == TargetAudience.ALL,
                    GlobalAnnouncement.target_audience == TargetAudience.ADMINS,
                )
            )
        elif user_role == "developer":
            stmt = stmt.where(
                or_(
                    GlobalAnnouncement.target_audience == TargetAudience.ALL,
                    GlobalAnnouncement.target_audience == TargetAudience.DEVELOPERS,
                )
            )
        else:
            stmt = stmt.where(GlobalAnnouncement.target_audience == TargetAudience.ALL)

        stmt = stmt.order_by(GlobalAnnouncement.start_date.desc())
        return list(db.scalars(stmt))

    @staticmethod
    def update_announcement(
        db: Session, db_announcement: GlobalAnnouncement, data: GlobalAnnouncementUpdate
    ) -> GlobalAnnouncement:
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_announcement, key, value)
        db.flush()
        db.refresh(db_announcement)
        return db_announcement

    @staticmethod
    def delete_announcement(db: Session, db_announcement: GlobalAnnouncement) -> None:
        db.delete(db_announcement)
        db.flush()
