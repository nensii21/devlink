from __future__ import annotations

"""
API Router for contribution heatmaps and streaks (#1040).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_database, get_optional_current_user
from app.models.user import User
from app.schemas.activity_heatmap import ActivityHeatmapResponse
from app.services.activity_heatmap_service import (
    DEFAULT_WINDOW_DAYS,
    MAX_WINDOW_DAYS,
    MIN_WINDOW_DAYS,
    ActivityHeatmapService,
)

router = APIRouter(
    prefix="/users",
    tags=["Activity Heatmap"],
)

_DAYS_QUERY = Query(
    DEFAULT_WINDOW_DAYS,
    ge=MIN_WINDOW_DAYS,
    le=MAX_WINDOW_DAYS,
    description="Size of the window in days, ending today (inclusive).",
)

_TYPES_QUERY = Query(
    None,
    description=(
        "Comma-separated ActivityType values to restrict the heatmap to, "
        "e.g. `project_created,comment_created`. Omit for all activity."
    ),
)


@router.get(
    "/me/activity-heatmap",
    response_model=ActivityHeatmapResponse,
    summary="Get your own contribution heatmap",
    description=(
        "Returns a day-by-day activity grid plus streak statistics for the "
        "authenticated user. Every day in the window is present, including "
        "days with zero activity."
    ),
)
def get_my_activity_heatmap(
    days: int = _DAYS_QUERY,
    activity_types: str | None = _TYPES_QUERY,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> ActivityHeatmapResponse:
    types = ActivityHeatmapService.parse_activity_types(activity_types)
    return ActivityHeatmapService.build(
        db, subject=current_user, days=days, activity_types=types
    )


@router.get(
    "/{username}/activity-heatmap",
    response_model=ActivityHeatmapResponse,
    summary="Get a builder's contribution heatmap",
    description=(
        "Returns a day-by-day activity grid plus streak statistics for the "
        "given user. Private profiles are only visible to their owner."
    ),
    responses={
        403: {"description": "Profile is private"},
        404: {"description": "User not found"},
    },
)
def get_user_activity_heatmap(
    username: str,
    days: int = _DAYS_QUERY,
    activity_types: str | None = _TYPES_QUERY,
    db: Session = Depends(get_database),
    current_user: User | None = Depends(get_optional_current_user),
) -> ActivityHeatmapResponse:
    subject = ActivityHeatmapService.get_user_or_404(db, username)
    ActivityHeatmapService.require_visible(subject, current_user, db)

    types = ActivityHeatmapService.parse_activity_types(activity_types)
    return ActivityHeatmapService.build(
        db, subject=subject, days=days, activity_types=types
    )
