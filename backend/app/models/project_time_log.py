from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProjectTimeLog(Base):
    """
    A single logged unit of work against a project (#1041).

    Duration is stored in whole minutes rather than hours-as-float: hours are a
    presentation concern, and summing floats across hundreds of entries invites
    the kind of drift where a summary and its own line items disagree by a
    fraction of an hour.
    """

    __tablename__ = "project_time_logs"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Foreign Keys
    # ==========================================================

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # A milestone can be deleted while the work that went into it still
    # happened, so the log survives with a null reference rather than
    # disappearing along with the milestone.
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_milestones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ==========================================================
    # Entry
    # ==========================================================

    minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # The day the work happened, which is frequently not the day it was
    # entered -- people log Friday's work on Monday morning.
    work_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_billable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    project = relationship("Project", backref="time_logs")
    user = relationship("User", backref="project_time_logs")
    milestone = relationship("Milestone", backref="time_logs")

    # ==========================================================
    # Audit
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        # The project report: everything logged on a project, by day.
        Index("ix_project_time_logs_project_date", "project_id", "work_date"),
        # "How much have I logged?" across a user's whole history.
        Index("ix_project_time_logs_user_date", "user_id", "work_date"),
        # The per-day cap check, which reads one user's entries on one project
        # for one day.
        Index(
            "ix_project_time_logs_project_user_date",
            "project_id",
            "user_id",
            "work_date",
        ),
    )

    @property
    def hours(self) -> float:
        """Minutes rendered as hours, rounded for display only."""
        return round(self.minutes / 60, 2)

    def __repr__(self) -> str:
        return f"<ProjectTimeLog(project={self.project_id}, user={self.user_id}, minutes={self.minutes})>"
