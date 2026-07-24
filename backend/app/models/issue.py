from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
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
    # Project
    # ----------------------------------------------------------

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project = relationship("Project", backref="issues")

    # ----------------------------------------------------------
    # Author
    # ----------------------------------------------------------

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author = relationship("User", backref="authored_issues")

    # ----------------------------------------------------------
    # Basic Information
    # ----------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ----------------------------------------------------------
    # Status & Priority
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # Labels (comma-separated)
    # ----------------------------------------------------------

    labels: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ----------------------------------------------------------
    # Embedding (stored as JSON array of floats)
    # ----------------------------------------------------------

    embedding: Mapped[str | None] = mapped_column(
        Text,
    )

    # ----------------------------------------------------------
    # Duplicate Detection
    # ----------------------------------------------------------

    is_duplicate_checked: Mapped[bool] = mapped_column(
        default=False,
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


class DuplicateSuggestion(Base):
    """
    Stores similarity relationships between issues.
    """

    __tablename__ = "duplicate_suggestions"

    # ----------------------------------------------------------
    # Primary Key
    # ----------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ----------------------------------------------------------
    # Source Issue (the one being created/checked)
    # ----------------------------------------------------------

    source_issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_issue = relationship(
        "Issue", foreign_keys=[source_issue_id], backref="suggestions_as_source"
    )

    # ----------------------------------------------------------
    # Duplicate Issue (the existing similar one)
    # ----------------------------------------------------------

    duplicate_issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    duplicate_issue = relationship(
        "Issue", foreign_keys=[duplicate_issue_id], backref="suggestions_as_duplicate"
    )

    # ----------------------------------------------------------
    # Similarity Score (0.0 to 1.0)
    # ----------------------------------------------------------

    similarity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # ----------------------------------------------------------
    # Audit
    # ----------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    def __repr__(self):
        return f"<DuplicateSuggestion(score={self.similarity_score})>"
