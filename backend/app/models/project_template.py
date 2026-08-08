from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProjectTemplate(Base):
    """
    Project Template model for the Templates Marketplace (#596).
    Allows developers to publish reusable project blueprints.
    """

    __tablename__ = "project_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="web-app",
        index=True,
    )

    tech_stack: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    features: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    repository_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    demo_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    clones_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    stars_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
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

    # Relationships
    author = relationship("User", lazy="joined")


class ProjectTemplateFavorite(Base):
    """
    Tracks template favorites/stars per user.
    """

    __tablename__ = "project_template_favorites"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_templates.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
