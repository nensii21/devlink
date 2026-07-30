from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class BookmarkTargetType(str, Enum):
    PROJECT = "project"
    FLARE = "flare"


class Bookmark(Base):
    """
    Saved items (projects, builder flares, and future content types).
    """

    __tablename__ = "bookmarks"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "target_type",
            "target_id",
            name="uq_user_target_bookmark",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Generic Target
    #
    # No DB-level FK/cascade here by design — target_id can point at
    # projects.id or builder_flares.id (or future content types).
    # Deleting a Project/BuilderFlare does NOT auto-delete its bookmarks;
    # BookmarkService is responsible for cleaning up orphaned bookmarks
    # (or resolving target_id lazily and treating a miss as "unavailable").
    # ==========================================================

    target_type: Mapped[BookmarkTargetType] = mapped_column(
        SqlEnum(BookmarkTargetType, name="bookmarktargettype"),
        nullable=False,
        index=True,
    )

    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    user = relationship(
        "User",
        backref="bookmarks",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<Bookmark(user={self.user_id}, "
            f"target={self.target_type.value}:{self.target_id})>"
        )
