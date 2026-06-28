from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    String,
    Text,
    func,
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

    BUILDER_FLARE_CREATED = "builder_flare_created"

    APPLICATION_SUBMITTED = "application_submitted"
    APPLICATION_ACCEPTED = "application_accepted"
    APPLICATION_REJECTED = "application_rejected"

    REPOSITORY_CONNECTED = "repository_connected"

    FOLLOWED_USER = "followed_user"

    MESSAGE_SENT = "message_sent"

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
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    # ==========================================================
    # Related Resources
    # ==========================================================

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
    )

    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="SET NULL"),
    )

    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
    )

    builder_flare_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("builder_flares.id", ondelete="SET NULL"),
    )

    # ==========================================================
    # Metadata
    # ==========================================================

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

    project = relationship(
        "Project",
        backref="activities",
    )

    organization = relationship(
        "Organization",
        backref="activities",
    )

    repository = relationship(
        "Repository",
        backref="activities",
    )

    application = relationship(
        "Application",
        backref="activities",
    )

    builder_flare = relationship(
        "BuilderFlare",
        backref="activities",
    )

    # ==========================================================
    # Audit
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<Activity("
            f"type='{self.activity_type.value}', "
            f"actor={self.actor_id}"
            f")>"
        )
