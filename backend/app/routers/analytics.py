from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.analytics import PlatformAnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "",
    response_model=PlatformAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Platform Analytics Dashboard Data",
    description="Returns tracked platform metrics including DAU, WAU, MAU, Retention, Conversion rates, and Project Growth trends.",
)
@router.get(
    "/",
    response_model=PlatformAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_platform_analytics(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(
        default=30, ge=1, le=365, description="Timeframe in days for daily breakdowns"
    ),
) -> PlatformAnalyticsResponse:
    return AnalyticsService.get_platform_analytics(db=db, days=days)


@router.get(
    "/dashboard",
    response_model=PlatformAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Analytics Dashboard Snapshot",
)
def get_analytics_dashboard(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=30, ge=1, le=365),
) -> PlatformAnalyticsResponse:
    return AnalyticsService.get_platform_analytics(db=db, days=days)


@router.get(
    "/overview",
    status_code=status.HTTP_200_OK,
    summary="Get Platform Metrics Overview",
)
def get_analytics_overview(
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    analytics = AnalyticsService.get_platform_analytics(db=db, days=30)
    return {
        "dau": analytics.active_users.dau,
        "wau": analytics.active_users.wau,
        "mau": analytics.active_users.mau,
        "retention_7d_pct": analytics.retention.retention_7d_pct,
        "retention_30d_pct": analytics.retention.retention_30d_pct,
        "profile_completion_pct": analytics.conversion.profile_completion_pct,
        "project_creator_pct": analytics.conversion.project_creator_pct,
        "total_projects": analytics.project_growth.total_projects,
        "project_growth_rate_pct": analytics.project_growth.growth_rate_pct,
    }
