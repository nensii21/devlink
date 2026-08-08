from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# Long enough for a considered answer, short enough that the thread stays
# readable. Enforced in the schema layer too, so the API rejects it with a 422
# rather than letting the database truncate or error.
MAX_BODY_LENGTH = 5000


class ProjectComment(Base):
    """
    A public, project-scoped discussion message (#930).

    Threading is deliberately one level deep: a comment either sits at the top
    of the thread or is a reply to one that does. Arbitrary nesting reads badly
    on narrow screens and makes both the query and the UI considerably more
    complicated for very little gain -- the pattern every comparable platform
    settles on.

    Deletion is soft. A removed comment is tombstoned rather than erased so
    that replies underneath it keep their parent and the thread does not
    develop holes.
    """

    __tablename__ = "project_comments"

    __table_args__ = (
        # The listing query: top-level comments for one project, newest first.
        Index("ix_project_comments_project_created", "project_id", "created_at"),
        # Fetching the replies belonging to a page of top-level comments.
        Index("ix_project_comments_parent_created", "parent_id", "created_at"),
    )

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

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Self-referential, and null for a top-level comment.
    #
    # ondelete is intentionally CASCADE: a parent is only ever hard-deleted
    # when its project or author is, and in that case the replies should go
    # too. Ordinary deletion goes through the soft-delete path below and never
    # removes the row.
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ==========================================================
    # Content
    # ==========================================================

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_edited: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ==========================================================
    # Soft Delete
    # ==========================================================

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ==========================================================
    # Timestamps
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

    # ==========================================================
    # Relationships
    # ==========================================================

    project = relationship("Project", foreign_keys=[project_id])

    author = relationship("User", foreign_keys=[author_id])

    deleted_by = relationship("User", foreign_keys=[deleted_by_id])

    replies = relationship(
        "ProjectComment",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="ProjectComment.created_at",
    )

    parent = relationship(
        "ProjectComment",
        back_populates="replies",
        remote_side=[id],
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        kind = "reply" if self.parent_id else "comment"
        return f"<ProjectComment {kind} {self.id} on project {self.project_id}>"
