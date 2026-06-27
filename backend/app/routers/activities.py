from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.activity import ActivityType
from app.models.user import User
from app.schemas.activity import (
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
)
from app.services.activity_service import ActivityService

router = APIRouter(
    prefix="/activities",
    tags=["Activities"],
)

@router.post(
    "/",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
def recent_activities(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):

    return ActivityService.list_recent_activities(
        db,
        limit,
    )
    
@router.get(
    "/user/{user_id}",
    response_model=list[ActivityResponse],
)
def user_activities(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):

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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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