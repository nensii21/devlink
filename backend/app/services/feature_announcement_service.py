from __future__ import annotations

import math
import uuid
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, selectinload

from app.models.feature_announcement import (
    AnnouncementCategory,
    FeatureAnnouncement,
    FeatureAnnouncementRead,
)
from app.schemas.feature_announcement import (
    FeatureAnnouncementCreate,
    FeatureAnnouncementListResponse,
    FeatureAnnouncementResponse,
    FeatureAnnouncementUpdate,
)
from app.utils.time import utcnow


class FeatureAnnouncementService:
    """
    Business logic for Platform Feature Announcement Center (#623).
    """

    @staticmethod
    def create_announcement(
        db: Session,
        admin_id: uuid.UUID,
        data: FeatureAnnouncementCreate,
    ) -> FeatureAnnouncement:
        published_at = data.published_at or utcnow()
        announcement = FeatureAnnouncement(
            created_by_id=admin_id,
            title=data.title,
            summary=data.summary,
            content=data.content,
            category=data.category,
            version=data.version,
            badge_label=data.badge_label,
            is_featured=data.is_featured,
            is_published=data.is_published,
            published_at=published_at,
        )
        db.add(announcement)
        db.flush()
        db.refresh(announcement)
        return announcement

    @staticmethod
    def get_announcement(
        db: Session,
        announcement_id: uuid.UUID,
    ) -> FeatureAnnouncement | None:
        stmt = (
            select(FeatureAnnouncement)
            .options(selectinload(FeatureAnnouncement.created_by))
            .where(FeatureAnnouncement.id == announcement_id)
        )
        return db.scalar(stmt)

    @staticmethod
    def update_announcement(
        db: Session,
        announcement: FeatureAnnouncement,
        data: FeatureAnnouncementUpdate,
    ) -> FeatureAnnouncement:
        update_data = data.model_dump(exclude_unset=True)
        for field, val in update_data.items():
            setattr(announcement, field, val)
        db.flush()
        db.refresh(announcement)
        return announcement

    @staticmethod
    def delete_announcement(
        db: Session,
        announcement: FeatureAnnouncement,
    ) -> None:
        db.delete(announcement)
        db.flush()

    @staticmethod
    def list_announcements(
        db: Session,
        user_id: uuid.UUID | None = None,
        category: AnnouncementCategory | None = None,
        q: str | None = None,
        is_featured: bool | None = None,
        page: int = 1,
        limit: int = 10,
        include_unpublished: bool = False,
    ) -> FeatureAnnouncementListResponse:
        page = max(1, page)
        limit = max(1, min(limit, 50))
        offset = (page - 1) * limit

        base_filter = []
        if not include_unpublished:
            base_filter.append(FeatureAnnouncement.is_published.is_(True))

        if category:
            base_filter.append(FeatureAnnouncement.category == category)

        if is_featured is not None:
            base_filter.append(FeatureAnnouncement.is_featured.is_(is_featured))

        if q:
            search_pattern = f"%{q.strip()}%"
            base_filter.append(
                or_(
                    FeatureAnnouncement.title.ilike(search_pattern),
                    FeatureAnnouncement.summary.ilike(search_pattern),
                    FeatureAnnouncement.content.ilike(search_pattern),
                    FeatureAnnouncement.version.ilike(search_pattern),
                )
            )

        # Count total
        count_stmt = select(func.count(FeatureAnnouncement.id)).where(*base_filter)
        total = db.scalar(count_stmt) or 0

        # Query items
        stmt = (
            select(FeatureAnnouncement)
            .options(selectinload(FeatureAnnouncement.created_by))
            .where(*base_filter)
            .order_by(
                FeatureAnnouncement.is_featured.desc(),
                FeatureAnnouncement.published_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        items = list(db.scalars(stmt))

        # Get user read IDs
        read_announcement_ids: set[uuid.UUID] = set()
        unread_count = 0
        if user_id:
            user_reads_stmt = select(FeatureAnnouncementRead.announcement_id).where(
                FeatureAnnouncementRead.user_id == user_id
            )
            read_announcement_ids = set(db.scalars(user_reads_stmt))

            # Total unread published announcements count
            all_published_stmt = select(FeatureAnnouncement.id).where(
                FeatureAnnouncement.is_published.is_(True)
            )
            all_published_ids = set(db.scalars(all_published_stmt))
            unread_count = len(all_published_ids - read_announcement_ids)

        # Convert to response schema with is_read
        response_items: list[FeatureAnnouncementResponse] = []
        for item in items:
            is_read = item.id in read_announcement_ids if user_id else False
            resp_item = FeatureAnnouncementResponse.model_validate(item)
            resp_item.is_read = is_read
            response_items.append(resp_item)

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return FeatureAnnouncementListResponse(
            items=response_items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            unread_count=unread_count,
        )

    @staticmethod
    def mark_as_read(
        db: Session,
        user_id: uuid.UUID,
        announcement_id: uuid.UUID,
    ) -> bool:
        stmt = select(FeatureAnnouncementRead).where(
            FeatureAnnouncementRead.user_id == user_id,
            FeatureAnnouncementRead.announcement_id == announcement_id,
        )
        existing = db.scalar(stmt)
        if not existing:
            read_entry = FeatureAnnouncementRead(
                user_id=user_id,
                announcement_id=announcement_id,
            )
            db.add(read_entry)
            db.flush()
        return True

    @staticmethod
    def mark_all_as_read(
        db: Session,
        user_id: uuid.UUID,
    ) -> int:
        published_stmt = select(FeatureAnnouncement.id).where(
            FeatureAnnouncement.is_published.is_(True)
        )
        all_ids = set(db.scalars(published_stmt))

        user_reads_stmt = select(FeatureAnnouncementRead.announcement_id).where(
            FeatureAnnouncementRead.user_id == user_id
        )
        read_ids = set(db.scalars(user_reads_stmt))

        unread_ids = all_ids - read_ids
        for ann_id in unread_ids:
            db.add(
                FeatureAnnouncementRead(
                    user_id=user_id,
                    announcement_id=ann_id,
                )
            )
        db.flush()
        return len(unread_ids)
