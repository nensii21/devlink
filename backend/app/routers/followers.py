from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.follower import (
    FollowActionResponse,
    FollowerResponse,
    FollowStatusResponse,
    UnfollowResponse,
)
from app.services.follower_service import FollowerService
from app.services.user_service import UserService

router = APIRouter(
    tags=["Followers"],
)


# ------------------------------------------------------------------
# POST /users/{user_id}/follow — Follow a user
# ------------------------------------------------------------------


@router.post(
    "/users/{user_id}/follow",
    response_model=FollowActionResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/followers/{user_id}",
    response_model=FollowActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def follow_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot follow yourself",
        )

    target_user = UserService.get_user(db, user_id)

    if target_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if not target_user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot follow a deactivated user",
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

    new_relationship = FollowerService.follow_user(
        db,
        current_user.id,
        user_id,
    )

    return FollowActionResponse(
        id=new_relationship.id,
        follower_id=new_relationship.follower_id,
        following_id=new_relationship.following_id,
        created_at=new_relationship.created_at,
        follower_count=FollowerService.follower_count(db, user_id),
        following_count=FollowerService.following_count(db, user_id),
    )


# ------------------------------------------------------------------
# DELETE /users/{user_id}/follow — Unfollow a user
# ------------------------------------------------------------------


@router.delete(
    "/users/{user_id}/follow",
    response_model=UnfollowResponse,
)
@router.delete(
    "/followers/{user_id}",
    response_model=UnfollowResponse,
)
def unfollow_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
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

    return UnfollowResponse(
        message="Unfollowed successfully",
        follower_count=FollowerService.follower_count(db, user_id),
        following_count=FollowerService.following_count(db, user_id),
    )


# ------------------------------------------------------------------
# GET /followers/ — Current user's following list
# ------------------------------------------------------------------


@router.get(
    "/followers",
    response_model=list[FollowerResponse],
)
@router.get(
    "/followers/",
    response_model=list[FollowerResponse],
)
def my_following(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return FollowerService.list_following(
        db,
        current_user.id,
    )


# ------------------------------------------------------------------
# GET /users/{user_id}/followers — User's followers
# ------------------------------------------------------------------


@router.get(
    "/users/{user_id}/followers",
    response_model=list[FollowerResponse],
)
@router.get(
    "/followers/{user_id}",
    response_model=list[FollowerResponse],
)
def user_followers(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    return FollowerService.list_followers(
        db,
        user_id,
    )


# ------------------------------------------------------------------
# GET /users/{user_id}/following — User's following list
# ------------------------------------------------------------------


@router.get(
    "/users/{user_id}/following",
    response_model=list[FollowerResponse],
)
@router.get(
    "/followers/{user_id}/following",
    response_model=list[FollowerResponse],
)
def user_following(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    return FollowerService.list_following(
        db,
        user_id,
    )


# ------------------------------------------------------------------
# GET /followers/{user_id}/count — Follower count
# ------------------------------------------------------------------


@router.get(
    "/followers/{user_id}/count",
)
def follower_count(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    return {
        "count": FollowerService.follower_count(
            db,
            user_id,
        )
    }


# ------------------------------------------------------------------
# GET /followers/{user_id}/following-count — Following count
# ------------------------------------------------------------------


@router.get(
    "/followers/{user_id}/following-count",
)
def following_count(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    return {
        "count": FollowerService.following_count(
            db,
            user_id,
        )
    }


# ------------------------------------------------------------------
# GET /users/{user_id}/follow-status — Check follow status
# ------------------------------------------------------------------


@router.get(
    "/users/{user_id}/follow-status",
    response_model=FollowStatusResponse,
)
@router.get(
    "/followers/{user_id}/is-following",
    response_model=FollowStatusResponse,
)
def is_following(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return FollowStatusResponse(
        is_following=FollowerService.is_following(
            db,
            current_user.id,
            user_id,
        ),
        follower_count=FollowerService.follower_count(db, user_id),
        following_count=FollowerService.following_count(db, user_id),
    )


# ------------------------------------------------------------------
# GET /followers/mutual/{user_id} — Mutual followers
# ------------------------------------------------------------------


@router.get(
    "/followers/mutual/{user_id}",
    response_model=list[FollowerResponse],
)
def mutual_followers(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return FollowerService.mutual_followers(
        db,
        current_user.id,
        user_id,
    )
