from __future__ import annotations

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.team_activity import (
    TeamActivityTimelineResponse,
    TeamActivityType,
    TeamActivityCreate,
    TeamActivityItem,
)
from app.services.team_activity_service import TeamActivityService

router = APIRouter(
    prefix="/projects/{project_id}/activity-timeline", tags=["Team Activity Timeline"]
)


@router.get(
    "",
    response_model=TeamActivityTimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Team Activity Timeline",
    description="Returns chronological team activity stream for a project team with support for pagination and type filtering.",
)
@router.get(
    "/",
    response_model=TeamActivityTimelineResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_team_activity_timeline(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1, description="Page number for pagination"),
    limit: int = Query(default=10, ge=1, le=50, description="Items per page"),
    activity_type: Optional[TeamActivityType] = Query(
        default=None, description="Filter by activity type"
    ),
) -> TeamActivityTimelineResponse:
    return TeamActivityService.get_project_timeline(
        db=db,
        project_id=project_id,
        page=page,
        limit=limit,
        activity_type=activity_type,
    )


@router.post(
    "",
    response_model=TeamActivityItem,
    status_code=status.HTTP_201_CREATED,
    summary="Log Team Activity Event",
    description="Creates a new chronological activity record for the project team.",
)
def create_team_activity_event(
    project_id: int,
    activity_in: TeamActivityCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TeamActivityItem:
    if not activity_in.actor_name:
        activity_in.actor_name = getattr(current_user, "username", "Team Member")
    return TeamActivityService.create_activity(
        db=db, project_id=project_id, activity_in=activity_in
    )
