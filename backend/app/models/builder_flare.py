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


class FlareStatus(str, Enum):
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"


class BuilderFlare(Base):
    """
    Builder Flare (Hiring Post)
    """

    __tablename__ = "builder_flares"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Flare Details
    # ==========================================================

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(
        String(150),
    )

    commitment: Mapped[str | None] = mapped_column(
        String(100),
    )

    experience_level: Mapped[str | None] = mapped_column(
        String(100),
    )

    # ==========================================================
    # Team
    # ==========================================================

    openings: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    applicants_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ==========================================================
    # Status
    # ==========================================================

    status: Mapped[FlareStatus] = mapped_column(
        SqlEnum(FlareStatus),
        default=FlareStatus.OPEN,
        nullable=False,
    )

    featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    remote: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    project = relationship(
        "Project",
        backref="builder_flares",
    )

    creator = relationship(
        "User",
        backref="builder_flares",
    )

    # ==========================================================
    # Audit
    # ==========================================================

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

    def __repr__(self):
        return (
            f"<BuilderFlare(title='{self.title}', "
            f"role='{self.role}')>"
        )