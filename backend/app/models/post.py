from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Post(Base):
    """
    Builder Feed Post / Flare
    """

    __tablename__ = "posts"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    # ==========================================================
    # Foreign Keys & Relationships
    # ==========================================================

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author = relationship(
        "User",
        backref="posts",
    )

    # ==========================================================
    # Details
    # ==========================================================

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String).with_variant(JSON, "sqlite"),
        default=list,
        server_default="[]",
        nullable=False,
    )

    likes_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    comments_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ==========================================================
    # Draft / Scheduling Status
    # ==========================================================

    # Status values: "draft", "published", "scheduled"
    status: Mapped[str] = mapped_column(
        String(20),
        default="published",
        nullable=False,
        index=True,
    )

    publish_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # ==========================================================
    # Audit
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<Post(author_id='{self.author_id}', status='{self.status}', created_at='{self.created_at}')>"
