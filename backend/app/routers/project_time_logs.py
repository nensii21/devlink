from __future__ import annotations

"""
API Router for project time tracking (#1041).
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_database
from app.models.user import User
from app.schemas.project_time_log import (
    TimeLogCreate,
    TimeLogList,
    TimeLogResponse,
    TimeLogSummary,
    TimeLogUpdate,
)
from app.services.project_time_log_service import ProjectTimeLogService

router = APIRouter(
    prefix="/projects/{project_id}/time-logs",
    tags=["Project Time Tracking"],
)


def _to_response(log) -> TimeLogResponse:
    """
    Build the response by hand so ``hours`` is derived from the stored integer
    rather than trusted from anywhere else.
    """
    return TimeLogResponse(
        id=log.id,
        project_id=log.project_id,
        user_id=log.user_id,
        milestone_id=log.milestone_id,
        minutes=log.minutes,
        hours=ProjectTimeLogService.to_hours(log.minutes),
        work_date=log.work_date,
        description=log.description,
        is_billable=log.is_billable,
        user=getattr(log, "user", None),
        created_at=log.created_at,
        updated_at=log.updated_at,
    )


@router.post(
    "",
    response_model=TimeLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log time against a project",
    description=(
        "Records a unit of work. Only active project members may log time. "
        "`work_date` must not be in the future or more than 90 days in the past, "
        "and one user's entries for a single day may not exceed 24 hours."
    ),
    responses={
        400: {"description": "Daily 24-hour limit would be exceeded"},
        403: {"description": "Not a member of this project"},
        404: {"description": "Project or milestone not found"},
    },
)
@router.post(
    "/",
    response_model=TimeLogResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_time_log(
    project_id: uuid.UUID,
    payload: TimeLogCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TimeLogResponse:
    log = ProjectTimeLogService.create_log(
        db, project_id=project_id, payload=payload, actor=current_user
    )
    return _to_response(log)


@router.get(
    "",
    response_model=TimeLogList,
    summary="List time entries for a project",
    description=(
        "Newest work first. `total` and `total_minutes` cover the whole "
        "filtered set, not just the returned page."
    ),
)
@router.get("/", response_model=TimeLogList, include_in_schema=False)
def list_time_logs(
    project_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: uuid.UUID | None = Query(None, description="Filter to one contributor"),
    milestone_id: uuid.UUID | None = Query(None, description="Filter to one milestone"),
    from_date: date | None = Query(
        None, description="Inclusive lower bound on work_date"
    ),
    to_date: date | None = Query(
        None, description="Inclusive upper bound on work_date"
    ),
    is_billable: bool | None = Query(None, description="Filter by billable flag"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TimeLogList:
    project = ProjectTimeLogService.get_project_or_404(db, project_id)
    ProjectTimeLogService.require_member(db, project, current_user)

    items, total, total_minutes = ProjectTimeLogService.list_logs(
        db,
        project_id=project_id,
        limit=limit,
        offset=offset,
        user_id=user_id,
        milestone_id=milestone_id,
        from_date=from_date,
        to_date=to_date,
        is_billable=is_billable,
    )
    return TimeLogList(
        items=[_to_response(log) for log in items],
        total=total,
        limit=limit,
        offset=offset,
        total_minutes=total_minutes,
    )


@router.get(
    "/me",
    response_model=TimeLogList,
    summary="List your own time entries on this project",
)
def list_my_time_logs(
    project_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TimeLogList:
    project = ProjectTimeLogService.get_project_or_404(db, project_id)
    ProjectTimeLogService.require_member(db, project, current_user)

    items, total, total_minutes = ProjectTimeLogService.list_logs(
        db,
        project_id=project_id,
        limit=limit,
        offset=offset,
        user_id=current_user.id,
        from_date=from_date,
        to_date=to_date,
    )
    return TimeLogList(
        items=[_to_response(log) for log in items],
        total=total,
        limit=limit,
        offset=offset,
        total_minutes=total_minutes,
    )


@router.get(
    "/summary",
    response_model=TimeLogSummary,
    summary="Effort summary for a project",
    description=(
        "Totals for the project with per-contributor and per-milestone "
        "breakdowns. Work with no milestone is grouped under a null "
        "`milestone_id` rather than dropped."
    ),
)
def get_time_log_summary(
    project_id: uuid.UUID,
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TimeLogSummary:
    project = ProjectTimeLogService.get_project_or_404(db, project_id)
    ProjectTimeLogService.require_member(db, project, current_user)

    return ProjectTimeLogService.summarise(
        db, project_id=project_id, from_date=from_date, to_date=to_date
    )


@router.get(
    "/{log_id}",
    response_model=TimeLogResponse,
    summary="Get one time entry",
)
def get_time_log(
    project_id: uuid.UUID,
    log_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TimeLogResponse:
    project = ProjectTimeLogService.get_project_or_404(db, project_id)
    ProjectTimeLogService.require_member(db, project, current_user)

    return _to_response(ProjectTimeLogService.get_log_or_404(db, project_id, log_id))


@router.patch(
    "/{log_id}",
    response_model=TimeLogResponse,
    summary="Edit a time entry",
    description="Only the person who logged the work may edit it.",
    responses={403: {"description": "Not your entry"}},
)
def update_time_log(
    project_id: uuid.UUID,
    log_id: uuid.UUID,
    payload: TimeLogUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> TimeLogResponse:
    log = ProjectTimeLogService.update_log(
        db, project_id=project_id, log_id=log_id, payload=payload, actor=current_user
    )
    return _to_response(log)


@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a time entry",
    description="The author may always delete their own entry; maintainers may delete anyone's.",
)
def delete_time_log(
    project_id: uuid.UUID,
    log_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    ProjectTimeLogService.delete_log(
        db, project_id=project_id, log_id=log_id, actor=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
