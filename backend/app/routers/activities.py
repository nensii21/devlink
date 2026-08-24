from __future__ import annotations

import uuid
from datetime import datetime

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query, status

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database, get_optional_current_user
from app.models.activity import ActivityType
from app.models.user import User
from app.schemas.activity import (
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
)
from app.services.activity_service import ActivityService
from app.core.cache import cached

router = APIRouter(
    prefix="",
    tags=["Activities"],
)


def check_activity_visibility(db: Session, actor_id: uuid.UUID, viewer: User | None) -> None:
    from app.services.user_service import UserService
    actor = UserService.get_user(db, actor_id)
    if actor:
        if actor.is_private:
            if viewer is None or viewer.id != actor.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this private profile.",
                )

        settings = actor.get_privacy_settings()
        activity_visibility = settings.get("activity", "public")
        
        is_visible = False
        if activity_visibility == "public":
            is_visible = True
        elif activity_visibility == "authenticated" and viewer is not None:
            is_visible = True
        elif activity_visibility == "followers" and viewer is not None:
            if viewer.id == actor.id or getattr(viewer, "is_superuser", False):
                is_visible = True
            else:
                from app.services.follower_service import FollowerService
                is_visible = FollowerService.is_following(
                    db, follower_id=viewer.id, following_id=actor.id
                )
        elif activity_visibility == "private":
            if viewer is not None and (viewer.id == actor.id or getattr(viewer, "is_superuser", False)):
                is_visible = True
        
        if not is_visible:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This user's activity details are private.",
            )


@router.post(
    "/",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):

    return ActivityService.create_activity(
        db=db,
        actor_id=current_user.id,
        activity=activity,
    )


@router.get(
    "/{activity_id}",
    response_model=ActivityResponse,
)
def get_activity(
    activity_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    activity = ActivityService.get_activity(
        db,
        activity_id,
    )

    if activity is None:
        raise HTTPException(
            status_code=404,
            detail="Activity not found",
        )

    return activity


@router.get(
    "/",
    response_model=list[ActivityResponse],
)
@cached(ttl=60, key_prefix="feed")
def get_feed(
    limit: int = Query(50, ge=1, le=100),
    cursor: datetime | None = Query(
        None, description="Cursor for pagination (created_at timestamp)"
    ),
    actor_id: uuid.UUID | None = Query(None, description="Filter by actor"),
    target_id: uuid.UUID | None = Query(None, description="Filter by target"),
    target_type: str | None = Query(None, description="Filter by target type"),
    activity_types: list[ActivityType] | None = Query(
        None, description="Filter by activity types"
    ),
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
):
    if actor_id:
        check_activity_visibility(db, actor_id, current_user)

    return ActivityService.list_activities(
        db=db,
        limit=limit,
        cursor=cursor,
        actor_id=actor_id,
        target_id=target_id,
        target_type=target_type,
        activity_types=activity_types,
    )


@router.get(
    "/user/{user_id}",
    response_model=list[ActivityResponse],
)
def user_activities(
    user_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
):
    check_activity_visibility(db, user_id, current_user)

    return ActivityService.list_user_activities(
        db,
        user_id,
    )


@router.get(
    "/project/{project_id}",
    response_model=list[ActivityResponse],
)
def project_activities(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return ActivityService.list_project_activities(
        db,
        project_id,
    )


@router.get(
    "/organization/{organization_id}",
    response_model=list[ActivityResponse],
)
def organization_activities(
    organization_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return ActivityService.list_organization_activities(
        db,
        organization_id,
    )


@router.get(
    "/repository/{repository_id}",
    response_model=list[ActivityResponse],
)
def repository_activities(
    repository_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    return ActivityService.list_repository_activities(
        db,
        repository_id,
    )


@router.get(
    "/type/{activity_type}",
    response_model=list[ActivityResponse],
)
def activities_by_type(
    activity_type: ActivityType,
    db: Session = Depends(get_database),
):

    return ActivityService.list_by_type(
        db,
        activity_type,
    )


@router.put(
    "/{activity_id}",
    response_model=ActivityResponse,
)
def update_activity(
    activity_id: uuid.UUID,
    activity: ActivityUpdate,
    db: Session = Depends(get_database),
):

    db_activity = ActivityService.get_activity(
        db,
        activity_id,
    )

    if db_activity is None:
        raise HTTPException(
            status_code=404,
            detail="Activity not found",
        )

    return ActivityService.update_activity(
        db,
        db_activity,
        activity,
    )


@router.delete(
    "/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_activity(
    activity_id: uuid.UUID,
    db: Session = Depends(get_database),
):

    db_activity = ActivityService.get_activity(
        db,
        activity_id,
    )

    if db_activity is None:
        raise HTTPException(
            status_code=404,
            detail="Activity not found",
        )

    ActivityService.delete_activity(
        db,
        db_activity,
    )
