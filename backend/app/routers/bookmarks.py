from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.user import User
from app.schemas.bookmark import BookmarkResponse, BookmarkTargetType
from app.services.bookmark_service import BookmarkService

router = APIRouter(
    prefix="/bookmarks",
    tags=["Bookmarks"],
)


@router.post(
    "/{target_type}/{target_id}",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bookmark(
    target_type: BookmarkTargetType,
    target_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    existing = BookmarkService.get_user_target_bookmark(
        db,
        current_user.id,
        target_type,
        target_id,
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Already bookmarked",
        )

    return BookmarkService.create_bookmark(
        db,
        current_user.id,
        target_type,
        target_id,
    )


@router.get(
    "/{bookmark_id}",
    response_model=BookmarkResponse,
)
def get_bookmark(
    bookmark_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    bookmark = BookmarkService.get_bookmark(
        db,
        bookmark_id,
    )

    if bookmark is None:
        raise HTTPException(
            status_code=404,
            detail="Bookmark not found",
        )

    return bookmark


@router.get(
    "/",
    response_model=list[BookmarkResponse],
)
def my_bookmarks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return BookmarkService.list_user_bookmarks(
        db,
        current_user.id,
    )


@router.get(
    "/{target_type}/{target_id}/all",
    response_model=list[BookmarkResponse],
)
def target_bookmarks(
    target_type: BookmarkTargetType,
    target_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return BookmarkService.list_target_bookmarks(
        db,
        target_type,
        target_id,
    )


@router.get(
    "/check/{target_type}/{target_id}",
)
def check_bookmark(
    target_type: BookmarkTargetType,
    target_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return {
        "bookmarked": BookmarkService.is_bookmarked(
            db,
            current_user.id,
            target_type,
            target_id,
        )
    }


@router.get(
    "/{target_type}/{target_id}/count",
)
def bookmark_count(
    target_type: BookmarkTargetType,
    target_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return {
        "count": BookmarkService.bookmark_count(
            db,
            target_type,
            target_id,
        )
    }


@router.delete(
    "/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_bookmark(
    bookmark_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    bookmark = BookmarkService.get_bookmark(
        db,
        bookmark_id,
    )

    if bookmark is None:
        raise HTTPException(
            status_code=404,
            detail="Bookmark not found",
        )

    BookmarkService.remove_bookmark(
        db,
        bookmark,
    )


@router.delete(
    "/me/all",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_all_bookmarks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    BookmarkService.remove_all_user_bookmarks(
        db,
        current_user.id,
    )
