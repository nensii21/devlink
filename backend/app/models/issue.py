from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    DUPLICATE = "duplicate"


class IssuePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueDifficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Issue(Base):
    """
    DevLink Issue Model
    """

    __tablename__ = "issues"

    # ----------------------------------------------------------
    # Primary Key
    # ----------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ----------------------------------------------------------
    # Relationships
    # ----------------------------------------------------------

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project = relationship("Project", backref="issues")

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author = relationship("User", backref="authored_issues")

    # ----------------------------------------------------------
    # Issue Details
    # ----------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[IssueStatus] = mapped_column(
        SqlEnum(IssueStatus),
        default=IssueStatus.OPEN,
        nullable=False,
        index=True,
    )

    priority: Mapped[IssuePriority] = mapped_column(
        SqlEnum(IssuePriority),
        default=IssuePriority.MEDIUM,
        nullable=False,
    )

    labels: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ----------------------------------------------------------
    # AI Difficulty Estimation
    # ----------------------------------------------------------

    difficulty: Mapped[IssueDifficulty | None] = mapped_column(
        SqlEnum(IssueDifficulty),
        nullable=True,
        index=True,
    )

    difficulty_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    difficulty_manual_override: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ----------------------------------------------------------
    # Audit
    # ----------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return f"<Issue(title='{self.title}')>"
