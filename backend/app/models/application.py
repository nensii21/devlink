from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
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


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    REVIEWING = "reviewing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(Base):
    """
    User application to a Builder Flare.
    """

    __tablename__ = "applications"

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

    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    flare_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("builder_flares.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Application
    # ==========================================================

    status: Mapped[ApplicationStatus] = mapped_column(
        SqlEnum(ApplicationStatus),
        default=ApplicationStatus.PENDING,
        nullable=False,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
    )

    portfolio_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    github_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    resume_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ==========================================================
    # Founder Notes
    # ==========================================================

    review_notes: Mapped[str | None] = mapped_column(
        Text,
    )

    shortlisted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    applicant = relationship(
        "User",
        backref="applications",
    )

    project = relationship(
        "Project",
        backref="applications",
    )

    flare = relationship(
        "BuilderFlare",
        backref="applications",
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

    def __repr__(self) -> str:
        return (
            f"<Application("
            f"applicant={self.applicant_id}, "
            f"status='{self.status.value}'"
            f")>"
        )
