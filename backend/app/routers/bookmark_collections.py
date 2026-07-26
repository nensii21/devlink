from __future__ import annotations

import uuid

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database
from app.models.user import User
from app.schemas.bookmark_collection import (
    BookmarkCollectionCreate,
    BookmarkCollectionResponse,
    BookmarkCollectionUpdate,
    BookmarkCollectionWithBookmarks,
)
from app.services.bookmark_collection_service import BookmarkCollectionService
from app.services.bookmark_service import BookmarkService

router = APIRouter(
    prefix="/bookmark-collections",
    tags=["Bookmark Collections"],
)


@router.get(
    "/",
    response_model=list[BookmarkCollectionResponse],
)
def list_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    BookmarkCollectionService.ensure_default_collection(db, current_user.id)
    db.flush()

    collections = BookmarkCollectionService.list_user_collections(
        db,
        current_user.id,
    )

    result = []
    for col in collections:
        count = BookmarkCollectionService.collection_bookmark_count(db, col.id)
        result.append(
            BookmarkCollectionResponse(
                id=col.id,
                user_id=col.user_id,
                name=col.name,
                is_default=col.is_default,
                bookmark_count=count,
                created_at=col.created_at,
                updated_at=col.updated_at,
            )
        )

    return result


@router.post(
    "/",
    response_model=BookmarkCollectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_collection(
    body: BookmarkCollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    try:
        collection = BookmarkCollectionService.create_collection(
            db, current_user.id, body.name
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    count = BookmarkCollectionService.collection_bookmark_count(db, collection.id)

    return BookmarkCollectionResponse(
        id=collection.id,
        user_id=collection.user_id,
        name=collection.name,
        is_default=collection.is_default,
        bookmark_count=count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.get(
    "/{collection_id}",
    response_model=BookmarkCollectionWithBookmarks,
)
def get_collection(
    collection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    collection = BookmarkCollectionService.get_collection_with_bookmarks(
        db,
        collection_id,
    )

    if collection is None or collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    return BookmarkCollectionWithBookmarks(
        id=collection.id,
        user_id=collection.user_id,
        name=collection.name,
        is_default=collection.is_default,
        bookmarks=collection.bookmarks,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.patch(
    "/{collection_id}",
    response_model=BookmarkCollectionResponse,
)
def rename_collection(
    collection_id: uuid.UUID,
    body: BookmarkCollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    collection = BookmarkCollectionService.get_collection(db, collection_id)

    if collection is None or collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    try:
        collection = BookmarkCollectionService.rename_collection(
            db, collection, body.name
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    count = BookmarkCollectionService.collection_bookmark_count(db, collection.id)

    return BookmarkCollectionResponse(
        id=collection.id,
        user_id=collection.user_id,
        name=collection.name,
        is_default=collection.is_default,
        bookmark_count=count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_collection(
    collection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    collection = BookmarkCollectionService.get_collection(db, collection_id)

    if collection is None or collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    try:
        BookmarkCollectionService.delete_collection(db, collection)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{collection_id}/bookmarks/{bookmark_id}",
    status_code=status.HTTP_201_CREATED,
)
def add_bookmark_to_collection(
    collection_id: uuid.UUID,
    bookmark_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    collection = BookmarkCollectionService.get_collection(db, collection_id)

    if collection is None or collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    bookmark = BookmarkService.get_bookmark(db, bookmark_id)

    if bookmark is None or bookmark.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )

    BookmarkCollectionService.add_bookmark_to_collection(db, collection_id, bookmark_id)

    count = BookmarkCollectionService.collection_bookmark_count(db, collection_id)

    return {"success": True, "bookmark_count": count}


@router.delete(
    "/{collection_id}/bookmarks/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_bookmark_from_collection(
    collection_id: uuid.UUID,
    bookmark_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    collection = BookmarkCollectionService.get_collection(db, collection_id)

    if collection is None or collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    removed = BookmarkCollectionService.remove_bookmark_from_collection(
        db, collection_id, bookmark_id
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found in collection",
        )


@router.get(
    "/bookmark/{bookmark_id}/collections",
    response_model=list[BookmarkCollectionResponse],
)
def get_bookmark_collections(
    bookmark_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    collection_ids = BookmarkCollectionService.bookmark_collection_ids(db, bookmark_id)

    collections = []
    for cid in collection_ids:
        col = BookmarkCollectionService.get_collection(db, cid)
        if col and col.user_id == current_user.id:
            count = BookmarkCollectionService.collection_bookmark_count(db, col.id)
            collections.append(
                BookmarkCollectionResponse(
                    id=col.id,
                    user_id=col.user_id,
                    name=col.name,
                    is_default=col.is_default,
                    bookmark_count=count,
                    created_at=col.created_at,
                    updated_at=col.updated_at,
                )
            )

    return collections
