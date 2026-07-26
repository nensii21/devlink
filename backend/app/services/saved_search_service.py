from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.saved_search import SavedSearch
from app.schemas.saved_search import SavedSearchCreate, SavedSearchUpdate


class DuplicateSavedSearchName(Exception):
    pass


class SavedSearchService:

    @staticmethod
    def list(db: Session, user_id: uuid.UUID) -> list[SavedSearch]:
        return list(
            db.scalars(
                select(SavedSearch)
                .where(SavedSearch.user_id == user_id)
                .order_by(SavedSearch.created_at.desc())
            )
        )

    @staticmethod
    def get(
        db: Session, search_id: uuid.UUID, user_id: uuid.UUID
    ) -> SavedSearch | None:
        return db.scalar(
            select(SavedSearch).where(
                SavedSearch.id == search_id,
                SavedSearch.user_id == user_id,
            )
        )

    @staticmethod
    def name_exists(db: Session, user_id: uuid.UUID, name: str) -> bool:
        return (
            db.scalar(
                select(SavedSearch).where(
                    SavedSearch.user_id == user_id,
                    SavedSearch.name == name.strip(),
                )
            )
            is not None
        )

    @staticmethod
    def create(
        db: Session, user_id: uuid.UUID, payload: SavedSearchCreate
    ) -> SavedSearch:
        saved = SavedSearch(
            user_id=user_id,
            name=payload.name.strip(),
            filters=payload.filters.model_dump(exclude_none=True),
        )
        db.add(saved)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise DuplicateSavedSearchName(payload.name.strip())
        db.refresh(saved)
        return saved

    @staticmethod
    def update(
        db: Session,
        saved: SavedSearch,
        payload: SavedSearchUpdate,
    ) -> SavedSearch:
        if payload.name is not None:
            saved.name = payload.name.strip()
        if payload.filters is not None:
            saved.filters = payload.filters.model_dump(exclude_none=True)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise DuplicateSavedSearchName(
                payload.name.strip() if payload.name else saved.name
            )
        db.refresh(saved)
        return saved

    @staticmethod
    def delete(db: Session, saved: SavedSearch) -> None:
        db.delete(saved)
        db.commit()
