from __future__ import annotations

import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.bookmark import Bookmark
from app.models.bookmark_collection import BookmarkCollection, CollectionBookmark


class BookmarkCollectionService:
    """
    Business logic for bookmark collections.
    """

    DEFAULT_COLLECTION_NAME = "All Bookmarks"

    @staticmethod
    def create_collection(
        db: Session,
        user_id: uuid.UUID,
        name: str,
    ) -> BookmarkCollection:
        existing = BookmarkCollectionService.get_collection_by_name(db, user_id, name)
        if existing:
            raise ValueError("A collection with this name already exists")

        collection = BookmarkCollection(
            user_id=user_id,
            name=name,
            is_default=False,
        )

        db.add(collection)
        db.flush()
        db.refresh(collection)

        return collection

    @staticmethod
    def ensure_default_collection(
        db: Session,
        user_id: uuid.UUID,
    ) -> BookmarkCollection:
        stmt = select(BookmarkCollection).where(
            and_(
                BookmarkCollection.user_id == user_id,
                BookmarkCollection.is_default,
            )
        )
        default = db.scalar(stmt)

        if default is None:
            default = BookmarkCollection(
                user_id=user_id,
                name=BookmarkCollectionService.DEFAULT_COLLECTION_NAME,
                is_default=True,
            )
            db.add(default)
            db.flush()
            db.refresh(default)

        return default

    @staticmethod
    def get_collection(
        db: Session,
        collection_id: uuid.UUID,
    ) -> BookmarkCollection | None:
        return db.get(BookmarkCollection, collection_id)

    @staticmethod
    def get_collection_by_name(
        db: Session,
        user_id: uuid.UUID,
        name: str,
    ) -> BookmarkCollection | None:
        stmt = select(BookmarkCollection).where(
            and_(
                BookmarkCollection.user_id == user_id,
                BookmarkCollection.name == name,
            )
        )
        return db.scalar(stmt)

    @staticmethod
    def list_user_collections(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[BookmarkCollection]:
        stmt = (
            select(BookmarkCollection)
            .where(BookmarkCollection.user_id == user_id)
            .order_by(BookmarkCollection.is_default.desc(), BookmarkCollection.name)
        )
        return list(db.scalars(stmt))

    @staticmethod
    def get_collection_with_bookmarks(
        db: Session,
        collection_id: uuid.UUID,
    ) -> BookmarkCollection | None:
        stmt = select(BookmarkCollection).where(BookmarkCollection.id == collection_id)
        collection = db.scalar(stmt)
        if collection is None:
            return None

        bookmark_stmt = (
            select(Bookmark)
            .join(
                CollectionBookmark,
                CollectionBookmark.bookmark_id == Bookmark.id,
            )
            .where(CollectionBookmark.collection_id == collection_id)
            .order_by(Bookmark.created_at.desc())
        )
        collection.bookmarks = list(db.scalars(bookmark_stmt))
        return collection

    @staticmethod
    def rename_collection(
        db: Session,
        collection: BookmarkCollection,
        new_name: str,
    ) -> BookmarkCollection:
        if collection.is_default:
            raise ValueError("Cannot rename the default collection")

        existing = BookmarkCollectionService.get_collection_by_name(
            db, collection.user_id, new_name
        )
        if existing and existing.id != collection.id:
            raise ValueError("A collection with this name already exists")

        collection.name = new_name
        db.flush()
        db.refresh(collection)

        return collection

    @staticmethod
    def delete_collection(
        db: Session,
        collection: BookmarkCollection,
    ) -> None:
        if collection.is_default:
            raise ValueError("Cannot delete the default collection")

        db.delete(collection)
        db.flush()

    @staticmethod
    def add_bookmark_to_collection(
        db: Session,
        collection_id: uuid.UUID,
        bookmark_id: uuid.UUID,
    ) -> CollectionBookmark:
        existing = db.get(CollectionBookmark, None)

        stmt = select(CollectionBookmark).where(
            and_(
                CollectionBookmark.collection_id == collection_id,
                CollectionBookmark.bookmark_id == bookmark_id,
            )
        )
        existing = db.scalar(stmt)

        if existing:
            return existing

        link = CollectionBookmark(
            collection_id=collection_id,
            bookmark_id=bookmark_id,
        )
        db.add(link)
        db.flush()
        db.refresh(link)

        return link

    @staticmethod
    def add_bookmark_to_default(
        db: Session,
        user_id: uuid.UUID,
        bookmark_id: uuid.UUID,
    ) -> CollectionBookmark | None:
        default = BookmarkCollectionService.ensure_default_collection(db, user_id)

        stmt = select(CollectionBookmark).where(
            and_(
                CollectionBookmark.collection_id == default.id,
                CollectionBookmark.bookmark_id == bookmark_id,
            )
        )
        existing = db.scalar(stmt)

        if existing:
            return existing

        link = CollectionBookmark(
            collection_id=default.id,
            bookmark_id=bookmark_id,
        )
        db.add(link)
        db.flush()
        return link

    @staticmethod
    def remove_bookmark_from_collection(
        db: Session,
        collection_id: uuid.UUID,
        bookmark_id: uuid.UUID,
    ) -> bool:
        stmt = select(CollectionBookmark).where(
            and_(
                CollectionBookmark.collection_id == collection_id,
                CollectionBookmark.bookmark_id == bookmark_id,
            )
        )
        link = db.scalar(stmt)

        if link is None:
            return False

        db.delete(link)
        db.flush()
        return True

    @staticmethod
    def collection_bookmark_count(
        db: Session,
        collection_id: uuid.UUID,
    ) -> int:
        stmt = select(func.count(CollectionBookmark.id)).where(
            CollectionBookmark.collection_id == collection_id
        )
        return db.scalar(stmt) or 0

    @staticmethod
    def bookmark_collection_ids(
        db: Session,
        bookmark_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        stmt = select(CollectionBookmark.collection_id).where(
            CollectionBookmark.bookmark_id == bookmark_id
        )
        return list(db.scalars(stmt))

    @staticmethod
    def is_bookmark_in_collection(
        db: Session,
        collection_id: uuid.UUID,
        bookmark_id: uuid.UUID,
    ) -> bool:
        stmt = select(CollectionBookmark).where(
            and_(
                CollectionBookmark.collection_id == collection_id,
                CollectionBookmark.bookmark_id == bookmark_id,
            )
        )
        return db.scalar(stmt) is not None
