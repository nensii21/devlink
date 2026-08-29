from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from app.database.base import Base


class PostComment(Base):
    """
    A comment on a feed post.

    ``POST /posts/{id}/comment`` used to accept a body, validate it, increment
    ``Post.comments_count`` and drop the text. There was no table to put it in
    and no endpoint to read it back, so the counter on the feed counted
    something that did not exist anywhere.
    """

    __tablename__ = "post_comments"

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

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

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

    # See the note on PostLike.post: the database owns this cascade.
    post = relationship(
        "Post",
        backref=backref("comments", cascade="all, delete-orphan", passive_deletes=True),
    )
    author = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<PostComment(post_id='{self.post_id}', author_id='{self.author_id}')>"
        )
