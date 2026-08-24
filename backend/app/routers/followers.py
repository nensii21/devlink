from __future__ import annotations

import uuid
from typing import Optional

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database, get_optional_current_user
from app.models.user import User
from app.schemas.follower import FollowerResponse, FollowStatusResponse
from app.services.follower_service import FollowerService

router = APIRouter(
    tags=["Followers"],
)


@router.post(
    "/{user_id}",
    response_model=FollowerResponse,
    status_code=status.HTTP_201_CREATED,
)
def follow_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot follow yourself",
        )

    relationship = FollowerService.get_relationship(
        db,
        current_user.id,
        user_id,
    )

    if relationship:
        raise HTTPException(
            status_code=400,
            detail="Already following this user",
        )

    # The notification is the service's job and has been all along. This used
    # to enqueue a second one here -- same event, different title, different
    # link -- so a follow put two rows in the recipient's list (#1317).
    return FollowerService.follow_user(
        db,
        current_user.id,
        user_id,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unfollow_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    relationship = FollowerService.get_relationship(
        db,
        current_user.id,
        user_id,
    )

    if relationship is None:
        raise HTTPException(
            status_code=404,
            detail="Follow relationship not found",
        )

    FollowerService.unfollow_user(
        db,
        relationship,
    )


@router.get(
    "/",
    response_model=list[FollowerResponse],
)
def my_following(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return FollowerService.list_following(
        db,
        current_user.id,
    )


@router.get(
    "/{user_id}",
    response_model=list[FollowerResponse],
)
def user_followers(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return FollowerService.list_followers(
        db,
        user_id,
    )


@router.get(
    "/{user_id}/following",
    response_model=list[FollowerResponse],
)
def user_following(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return FollowerService.list_following(
        db,
        user_id,
    )


@router.get(
    "/{user_id}/count",
)
def follower_count(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return {
        "count": FollowerService.follower_count(
            db,
            user_id,
        )
    }


@router.get(
    "/{user_id}/following-count",
)
def following_count(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return {
        "count": FollowerService.following_count(
            db,
            user_id,
        )
    }


@router.get(
    "/{user_id}/is-following",
)
def is_following(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return {
        "following": FollowerService.is_following(
            db,
            current_user.id,
            user_id,
        )
    }


@router.get(
    "/mutual/{user_id}",
    response_model=list[FollowerResponse],
)
def mutual_followers(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):

    return FollowerService.mutual_followers(
        db,
        current_user.id,
        user_id,
    )


@router.get(
    "/{user_id}/status",
    response_model=FollowStatusResponse,
    summary="Get combined follow status for a user",
)
def get_follow_status(
    user_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_database),
):
    """
    Returns is_following, follower_count, and following_count in a single
    request.  is_following is always False when the caller is not authenticated.
    """
    is_following = (
        FollowerService.is_following(db, current_user.id, user_id)
        if current_user is not None
        else False
    )
    return FollowStatusResponse(
        is_following=is_following,
        follower_count=FollowerService.follower_count(db, user_id),
        following_count=FollowerService.following_count(db, user_id),
    )
