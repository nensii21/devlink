from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    String,
    Text,
    func,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ActivityType(str, Enum):
    USER_REGISTERED = "user_registered"
    PROFILE_UPDATED = "profile_updated"

    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_ARCHIVED = "project_archived"
    PROJECT_MILESTONE = "project_milestone"

    BUILDER_FLARE_CREATED = "builder_flare_created"

    APPLICATION_SUBMITTED = "application_submitted"
    APPLICATION_ACCEPTED = "application_accepted"
    APPLICATION_REJECTED = "application_rejected"

    TEAM_INVITATION = "team_invitation"

    REPOSITORY_CONNECTED = "repository_connected"

    FOLLOWED_USER = "followed_user"

    MESSAGE_SENT = "message_sent"
    COMMENT_CREATED = "comment_created"
    DISCUSSION_CREATED = "discussion_created"

    ORGANIZATION_CREATED = "organization_created"

    SYSTEM = "system"


class Activity(Base):
    """
    Activity Feed Model
    """

    __tablename__ = "activities"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Actor
    # ==========================================================

    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Activity
    # ==========================================================

    activity_type: Mapped[ActivityType] = mapped_column(
        SqlEnum(ActivityType),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    # ==========================================================
    # Generic Target
    # ==========================================================

    target_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    target_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # ==========================================================
    # Metadata
    # ==========================================================

    meta: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        name="metadata",
        default=dict,
        server_default="{}",
        nullable=False,
    )

    icon: Mapped[str | None] = mapped_column(
        String(100),
    )

    color: Mapped[str | None] = mapped_column(
        String(30),
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    actor = relationship(
        "User",
        backref="activities",
    )

    # ==========================================================
    # Audit
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_activities_type_created", "activity_type", "created_at"),
    )

    def __repr__(self):
        return f"<Activity(type='{self.activity_type.value}', actor={self.actor_id})>"
