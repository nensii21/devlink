"""
API Router for Project Milestone Management (#618)
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_database
from app.models.user import User
from app.schemas.milestone import (
    MilestoneCreate,
    MilestoneProgressResponse,
    MilestoneResponse,
    MilestoneTimelineResponse,
    MilestoneUpdate,
)
from app.services.project_milestone_service import ProjectMilestoneService

router = APIRouter(
    prefix="/projects/{project_id}/milestones",
    tags=["Project Milestones"],
)


@router.get(
    "",
    response_model=list[MilestoneResponse],
    summary="List project milestones",
    description="Retrieve all milestones for a project with optional filtering for archived/completed milestones.",
)
@router.get(
    "/",
    response_model=list[MilestoneResponse],
    include_in_schema=False,
)
def list_milestones(
    project_id: uuid.UUID,
    include_archived: bool = Query(
        False, description="Set to true to include archived milestones"
    ),
    is_completed: Optional[bool] = Query(
        None, description="Filter by completion status"
    ),
    db: Session = Depends(get_database),
) -> list[MilestoneResponse]:
    milestones = ProjectMilestoneService.list_milestones(
        db,
        project_id=project_id,
        include_archived=include_archived,
        is_completed=is_completed,
    )
    return [MilestoneResponse.model_validate(m) for m in milestones]


@router.post(
    "",
    response_model=MilestoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create milestone",
    description="Create a new milestone for the project. Only project owners and maintainers can create milestones.",
)
@router.post(
    "/",
    response_model=MilestoneResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_milestone(
    project_id: uuid.UUID,
    milestone_in: MilestoneCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> MilestoneResponse:
    milestone = ProjectMilestoneService.create_milestone(
        db, project_id=project_id, milestone_in=milestone_in, actor=current_user
    )
    return MilestoneResponse.model_validate(milestone)


@router.get(
    "/progress",
    response_model=MilestoneProgressResponse,
    summary="Get milestone progress metrics",
    description="Calculates total milestones, completed count, active/archived breakdown, overdue count, and completion percentage.",
)
def get_milestone_progress(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
) -> MilestoneProgressResponse:
    return ProjectMilestoneService.calculate_progress(db, project_id=project_id)


@router.get(
    "/timeline",
    response_model=MilestoneTimelineResponse,
    summary="Get milestone timeline view",
    description="Returns milestones formatted in a chronological timeline view with status tags ('upcoming', 'overdue', 'completed', 'archived') and remaining days.",
)
def get_milestone_timeline(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
) -> MilestoneTimelineResponse:
    return ProjectMilestoneService.get_timeline(db, project_id=project_id)


@router.get(
    "/{milestone_id}",
    response_model=MilestoneResponse,
    summary="Get milestone details",
)
def get_milestone(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    db: Session = Depends(get_database),
) -> MilestoneResponse:
    milestone = ProjectMilestoneService.get_milestone_or_404(
        db, project_id, milestone_id
    )
    return MilestoneResponse.model_validate(milestone)


@router.patch(
    "/{milestone_id}",
    response_model=MilestoneResponse,
    summary="Update milestone",
    description="Update milestone title, description, due date, completion status, or archive status.",
)
def update_milestone(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    milestone_in: MilestoneUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> MilestoneResponse:
    milestone = ProjectMilestoneService.update_milestone(
        db,
        project_id=project_id,
        milestone_id=milestone_id,
        milestone_in=milestone_in,
        actor=current_user,
    )
    return MilestoneResponse.model_validate(milestone)


@router.post(
    "/{milestone_id}/archive",
    response_model=MilestoneResponse,
    summary="Archive milestone",
    description="Archive a completed or obsolete milestone.",
)
def archive_milestone(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> MilestoneResponse:
    milestone = ProjectMilestoneService.archive_milestone(
        db,
        project_id=project_id,
        milestone_id=milestone_id,
        actor=current_user,
        archive=True,
    )
    return MilestoneResponse.model_validate(milestone)


@router.post(
    "/{milestone_id}/unarchive",
    response_model=MilestoneResponse,
    summary="Unarchive milestone",
    description="Restore an archived milestone back to active status.",
)
def unarchive_milestone(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> MilestoneResponse:
    milestone = ProjectMilestoneService.archive_milestone(
        db,
        project_id=project_id,
        milestone_id=milestone_id,
        actor=current_user,
        archive=False,
    )
    return MilestoneResponse.model_validate(milestone)


@router.delete(
    "/{milestone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete milestone",
    description="Delete a milestone from the project.",
)
def delete_milestone(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    ProjectMilestoneService.delete_milestone(
        db, project_id=project_id, milestone_id=milestone_id, actor=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
