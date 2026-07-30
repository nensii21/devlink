from __future__ import annotations

import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.bookmark import Bookmark, BookmarkTargetType


class BookmarkService:
    """
    Business logic for bookmarks (projects, builder flares, and future
    content types) via a polymorphic target_type/target_id pair.
    """

    @staticmethod
    def create_bookmark(
        db: Session,
        user_id: uuid.UUID,
        target_type: BookmarkTargetType,
        target_id: uuid.UUID,
    ) -> Bookmark:

        bookmark = Bookmark(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
        )

        db.add(bookmark)
        db.flush()
        db.refresh(bookmark)

        return bookmark

    @staticmethod
    def get_bookmark(
        db: Session,
        bookmark_id: uuid.UUID,
    ) -> Bookmark | None:

        return db.get(Bookmark, bookmark_id)

    @staticmethod
    def get_user_target_bookmark(
        db: Session,
        user_id: uuid.UUID,
        target_type: BookmarkTargetType,
        target_id: uuid.UUID,
    ) -> Bookmark | None:

        stmt = select(Bookmark).where(
            and_(
                Bookmark.user_id == user_id,
                Bookmark.target_type == target_type,
                Bookmark.target_id == target_id,
            )
        )

        return db.scalar(stmt)

    @staticmethod
    def list_user_bookmarks(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[Bookmark]:

        stmt = (
            select(Bookmark)
            .where(Bookmark.user_id == user_id)
            .order_by(Bookmark.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_target_bookmarks(
        db: Session,
        target_type: BookmarkTargetType,
        target_id: uuid.UUID,
    ) -> list[Bookmark]:

        stmt = select(Bookmark).where(
            and_(
                Bookmark.target_type == target_type,
                Bookmark.target_id == target_id,
            )
        )

        return list(db.scalars(stmt))

    @staticmethod
    def is_bookmarked(
        db: Session,
        user_id: uuid.UUID,
        target_type: BookmarkTargetType,
        target_id: uuid.UUID,
    ) -> bool:

        stmt = select(Bookmark).where(
            and_(
                Bookmark.user_id == user_id,
                Bookmark.target_type == target_type,
                Bookmark.target_id == target_id,
            )
        )

        return db.scalar(stmt) is not None

    @staticmethod
    def bookmark_count(
        db: Session,
        target_type: BookmarkTargetType,
        target_id: uuid.UUID,
    ) -> int:

        stmt = select(Bookmark).where(
            and_(
                Bookmark.target_type == target_type,
                Bookmark.target_id == target_id,
            )
        )

        return len(list(db.scalars(stmt)))

    @staticmethod
    def remove_bookmark(
        db: Session,
        db_bookmark: Bookmark,
    ) -> None:

        db.delete(db_bookmark)
        db.flush()

    @staticmethod
    def remove_all_user_bookmarks(
        db: Session,
        user_id: uuid.UUID,
    ) -> None:

        stmt = select(Bookmark).where(Bookmark.user_id == user_id)

        bookmarks = list(db.scalars(stmt))

        for bookmark in bookmarks:
            db.delete(bookmark)

        db.flush()
