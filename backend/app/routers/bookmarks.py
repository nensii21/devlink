from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.bookmark import BookmarkResponse
from app.services.bookmark_service import BookmarkService

router = APIRouter(
    prefix="/bookmarks",
    tags=["Bookmarks"],
)


@router.post(
    "/project/{project_id}",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
)
def bookmark_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    existing = BookmarkService.get_user_project_bookmark(
        db,
        current_user.id,
        project_id,
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Project already bookmarked",
        )

    return BookmarkService.create_bookmark(
        db,
        current_user.id,
        project_id,
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
    "/project/{project_id}",
    response_model=list[BookmarkResponse],
)
def project_bookmarks(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return BookmarkService.list_project_bookmarks(
        db,
        project_id,
    )


@router.get(
    "/check/{project_id}",
)
def check_bookmark(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return {
        "bookmarked": BookmarkService.is_bookmarked(
            db,
            current_user.id,
            project_id,
        )
    }


@router.get(
    "/project/{project_id}/count",
)
def bookmark_count(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return {
        "count": BookmarkService.bookmark_count(
            db,
            project_id,
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
