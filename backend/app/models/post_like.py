from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from app.database.base import Base


class PostLike(Base):
    """
    One row per (post, user) pair that has liked a post.

    Before this existed, ``Post.likes_count`` was the only record of a like,
    which meant the question "has this user liked this post?" had no answer.
    ``POST /posts/{id}/like`` could only increment, so calling it twice meant
    two likes from one account, and ``DELETE`` could only decrement, so any
    authenticated user could walk a post's count down to zero.

    The unique constraint is what makes both operations idempotent, and it is
    enforced by the database rather than by a preceding SELECT so two
    concurrent likes cannot both pass the check.
    """

    __tablename__ = "post_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_likes_post_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # `passive_deletes` hands the cascade to the FK's ON DELETE CASCADE
    # instead of having the ORM null out `post_id` first -- which the NOT NULL
    # constraint refuses, so deleting a liked post failed outright.
    post = relationship(
        "Post",
        backref=backref("likes", cascade="all, delete-orphan", passive_deletes=True),
    )
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<PostLike(post_id='{self.post_id}', user_id='{self.user_id}')>"
