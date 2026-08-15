from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.project_collaboration_metrics import (
    ProjectCollaborationMetricsResponse,
)
from app.services.project_collaboration_metrics_service import (
    ProjectCollaborationMetricsService,
)

router = APIRouter(
    prefix="/projects/{project_id}/collaboration-metrics",
    tags=["Project Collaboration Metrics"],
)


@router.get(
    "",
    response_model=ProjectCollaborationMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Project Collaboration Metrics",
    description="Returns key team engagement metrics including active members, response times, messages, completed tasks, applications, and daily activity.",
)
@router.get(
    "/",
    response_model=ProjectCollaborationMetricsResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_project_collaboration_metrics(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProjectCollaborationMetricsResponse:
    return ProjectCollaborationMetricsService.get_metrics_for_project(
        db=db, project_id=project_id
    )
