from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# A profile shop-window, not a project list. Six is enough to show range and
# few enough that a visitor reads all of them.
MAX_PINNED_PROJECTS = 6


class PinnedProject(Base):
    """
    A project a user has chosen to feature on their profile (#1042).
    """

    __tablename__ = "pinned_projects"

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

    user_id: Mapped[uuid.UUID] = mapped_column(
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

    # ==========================================================
    # Ordering
    # ==========================================================

    # 0-based, contiguous. There is deliberately no unique constraint on
    # (user_id, position): a reorder has to pass through states where two rows
    # briefly share a slot, and a non-deferrable unique index would reject the
    # write halfway. The service owns compaction instead.
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    user = relationship("User", backref="pinned_projects")
    project = relationship("Project", backref="pinned_by")

    # ==========================================================
    # Audit
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        # One pin per project per user. This *is* safe to enforce in the
        # database -- unlike position, it never legitimately collides.
        UniqueConstraint(
            "user_id", "project_id", name="uq_pinned_projects_user_project"
        ),
        # The read path: one user's pins in display order.
        Index("ix_pinned_projects_user_position", "user_id", "position"),
    )

    def __repr__(self) -> str:
        return f"<PinnedProject(user={self.user_id}, project={self.project_id}, position={self.position})>"
