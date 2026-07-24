from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class BookmarkCollection(Base):
    """
    A named group of bookmarks belonging to a user.
    """

    __tablename__ = "bookmark_collections"

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

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    is_default: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

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

    user = relationship(
        "User",
        backref="bookmark_collections",
    )

    bookmarks = relationship(
        "Bookmark",
        secondary="collection_bookmarks",
        backref="collections",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "name",
            name="uq_user_collection_name",
        ),
    )

    def __repr__(self):
        return f"<BookmarkCollection(name={self.name}, user={self.user_id})>"


class CollectionBookmark(Base):
    """
    Junction table linking bookmark collections to bookmarks.
    """

    __tablename__ = "collection_bookmarks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookmark_collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    bookmark_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookmarks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    collection = relationship(
        "BookmarkCollection",
        backref="collection_bookmarks",
    )

    bookmark = relationship(
        "Bookmark",
        backref="collection_memberships",
    )

    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "bookmark_id",
            name="uq_collection_bookmark",
        ),
    )

    def __repr__(self):
        return f"<CollectionBookmark(collection={self.collection_id}, bookmark={self.bookmark_id})>"
