from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AnnouncementCategory(str, Enum):
    FEATURE = "feature"
    RELEASE_NOTES = "release_notes"
    CHANGELOG = "changelog"
    ROADMAP = "roadmap"


class FeatureAnnouncement(Base):
    """
    Platform Feature Announcement Model (#623)
    """

    __tablename__ = "feature_announcements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[AnnouncementCategory] = mapped_column(
        SqlEnum(AnnouncementCategory),
        default=AnnouncementCategory.FEATURE,
        nullable=False,
        index=True,
    )

    version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    badge_label: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    created_by = relationship("User", foreign_keys=[created_by_id])
    read_records = relationship(
        "FeatureAnnouncementRead",
        back_populates="announcement",
        cascade="all, delete-orphan",
    )


class FeatureAnnouncementRead(Base):
    """
    Tracks which users have read which feature announcements (#623)
    """

    __tablename__ = "feature_announcement_reads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    announcement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feature_announcements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    announcement = relationship("FeatureAnnouncement", back_populates="read_records")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "announcement_id", name="uq_user_feature_announcement_read"
        ),
    )
