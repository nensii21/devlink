from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_database, require_project_permission
from app.models.user import User
from app.schemas.project_dashboard import ProjectDashboardResponse
from app.schemas.milestone import MilestoneCreate, MilestoneResponse
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse
from app.services.project_dashboard_service import ProjectDashboardService

router = APIRouter(prefix="/projects", tags=["Project Dashboard"])


@router.get(
    "/{project_id}/dashboard",
    response_model=ProjectDashboardResponse,
    summary="Get Project Team Workspace Dashboard Data",
)
def get_project_dashboard(
    project_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_project_permission("project:view")),
):
    """
    Retrieves centralized team workspace dashboard data for a project.
    Only accessible by active project members and owners.
    """
    dashboard_data = ProjectDashboardService.get_dashboard_data(db, project_id)
    if dashboard_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return dashboard_data


@router.post(
    "/{project_id}/milestones",
    response_model=MilestoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Milestone to Project",
)
def create_project_milestone(
    project_id: uuid.UUID,
    milestone_in: MilestoneCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_project_permission("project:update")),
):
    """
    Creates a new project milestone.
    Restricted to Owners, Co-Owners, Admins, and Maintainers.
    """
    return ProjectDashboardService.create_milestone(
        db=db,
        project_id=project_id,
        actor_id=current_user.id,
        milestone_in=milestone_in,
    )


@router.patch(
    "/{project_id}/milestones/{milestone_id}/complete",
    response_model=MilestoneResponse,
    summary="Mark Milestone as Completed or Reopened",
)
def complete_project_milestone(
    project_id: uuid.UUID,
    milestone_id: uuid.UUID,
    is_completed: bool,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_project_permission("project:update")),
):
    """
    Marks a milestone as completed or reopens it.
    Restricted to Owners, Co-Owners, Admins, and Maintainers.
    """
    milestone = ProjectDashboardService.complete_milestone(
        db=db,
        project_id=project_id,
        milestone_id=milestone_id,
        actor_id=current_user.id,
        is_completed=is_completed,
    )
    if milestone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found in this project",
        )
    return milestone


@router.post(
    "/{project_id}/announcements",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post Announcement to Project",
)
def create_project_announcement(
    project_id: uuid.UUID,
    announcement_in: AnnouncementCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_project_permission("project:update")),
):
    """
    Posts a team announcement on the project dashboard.
    Restricted to Owners, Co-Owners, Admins, and Maintainers.
    """
    return ProjectDashboardService.create_announcement(
        db=db,
        project_id=project_id,
        author_id=current_user.id,
        announcement_in=announcement_in,
    )
