from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# Forward reference for type annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User


class ProjectStage(str, Enum):
    IDEA = "idea"
    VALIDATION = "validation"
    MVP = "mvp"
    BETA = "beta"
    PRODUCTION = "production"


class ProjectVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class Project(Base):
    """
    DevLink Project Model
    """

    __tablename__ = "projects"

    # ----------------------------------------------------------
    # Primary Key
    # ----------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ----------------------------------------------------------
    # Owner
    # ----------------------------------------------------------

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner = relationship("User", backref="projects")

    # ----------------------------------------------------------
    # Basic Information
    # ----------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
        index=True,
    )

    tagline: Mapped[str | None] = mapped_column(
        String(255),
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ----------------------------------------------------------
    # Project Details
    # ----------------------------------------------------------

    stage: Mapped[ProjectStage] = mapped_column(
        SqlEnum(ProjectStage),
        default=ProjectStage.IDEA,
        nullable=False,
    )

    visibility: Mapped[ProjectVisibility] = mapped_column(
        SqlEnum(ProjectVisibility),
        default=ProjectVisibility.PUBLIC,
        nullable=False,
    )

    tech_stack: Mapped[str | None] = mapped_column(
        Text,
    )

    repository_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    website_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    demo_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ----------------------------------------------------------
    # Team
    # ----------------------------------------------------------

    team_size: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    max_team_size: Mapped[int] = mapped_column(
        Integer,
        default=5,
    )

    hiring: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    # ----------------------------------------------------------
    # Media
    # ----------------------------------------------------------

    logo_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    banner_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ----------------------------------------------------------
    # Statistics
    # ----------------------------------------------------------

    stars: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    views: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    applications_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # ----------------------------------------------------------
    # Status
    # ----------------------------------------------------------

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    # ----------------------------------------------------------
    # Soft Delete
    # ----------------------------------------------------------

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    deleted_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[deleted_by_id],
    )

    # ----------------------------------------------------------
    # Audit
    # ----------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return f"<Project(title='{self.title}')>"
