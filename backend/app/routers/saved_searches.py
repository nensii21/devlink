from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.models.user import User
from app.schemas.saved_search import (
    SavedSearchCreate,
    SavedSearchResponse,
    SavedSearchUpdate,
)
from app.services.saved_search_service import (
    SavedSearchService,
    DuplicateSavedSearchName,
)

router = APIRouter(
    prefix="/saved-searches",
    tags=["Saved Searches"],
)


def _get_or_404(db: Session, search_id: uuid.UUID, user_id: uuid.UUID):
    saved = SavedSearchService.get(db, search_id, user_id)
    if saved is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found."
        )
    return saved


@router.get("/", response_model=list[SavedSearchResponse])
def list_saved_searches(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    return SavedSearchService.list(db, current_user.id)


@router.post(
    "/", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED
)
def create_saved_search(
    payload: SavedSearchCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if SavedSearchService.name_exists(db, current_user.id, payload.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A saved search named '{payload.name.strip()}' already exists.",
        )
    try:
        return SavedSearchService.create(db, current_user.id, payload)
    except DuplicateSavedSearchName:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A saved search named '{payload.name.strip()}' already exists.",
        )


@router.get("/{search_id}", response_model=SavedSearchResponse)
def get_saved_search(
    search_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    return _get_or_404(db, search_id, current_user.id)


@router.patch("/{search_id}", response_model=SavedSearchResponse)
def update_saved_search(
    search_id: uuid.UUID,
    payload: SavedSearchUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    saved = _get_or_404(db, search_id, current_user.id)

    if payload.name and payload.name.strip() != saved.name:
        if SavedSearchService.name_exists(db, current_user.id, payload.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A saved search named '{payload.name.strip()}' already exists.",
            )
    try:
        return SavedSearchService.update(db, saved, payload)
    except DuplicateSavedSearchName:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A saved search named '{payload.name.strip()}' already exists.",
        )


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_search(
    search_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    saved = _get_or_404(db, search_id, current_user.id)
    SavedSearchService.delete(db, saved)
