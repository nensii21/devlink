from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import (
    get_current_admin,
    get_current_user,
    get_optional_current_user,
)
from app.models.user import User
from app.schemas.analytics import (
    PlatformAnalyticsResponse,
    PlatformSocialProofResponse,
)
from app.schemas.community_stats import CommunityStatsResponse
from app.services.analytics_service import AnalyticsService
from app.services.community_stats_service import CommunityStatsService
from app.schemas.request_analytics import RequestAnalyticsResponse
from app.services.request_analytics_service import RequestAnalyticsService
from app.schemas.profile_analytics import ProfileAnalyticsResponse, TrackClickRequest

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


@router.get(
    "/social-proof",
    response_model=PlatformSocialProofResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Public Social Proof & Platform Growth Stats (#761)",
    description="Returns platform adoption numbers for the landing page social proof counters: developers, projects, teams, organizations, and hackathons.",
)
@router.get(
    "/social-proof/",
    response_model=PlatformSocialProofResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_social_proof(
    db: Annotated[Session, Depends(get_db)],
) -> PlatformSocialProofResponse:
    return AnalyticsService.get_social_proof(db=db)


@router.get(
    "/community/stats",
    response_model=CommunityStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Community Statistics Dashboard Data",
    description="Returns platform-wide community statistics including developer counts, active projects, teams, opportunities, monthly contributions and registrations, plus popular skills and trending technologies. Admin only.",
)
@router.get(
    "/community/stats/",
    response_model=CommunityStatsResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_community_stats(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
    days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Timeframe in days for trending technologies",
    ),
) -> CommunityStatsResponse:
    return CommunityStatsService.get_community_stats(db=db, days=days)


# ==========================================================
# API Request Analytics
# ==========================================================


@router.get(
    "/requests",
    response_model=RequestAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get API Request Analytics",
    description=(
        "Admin endpoint returning API request metrics: total volume, average "
        "response time, error rate, active users, rate-limited requests, "
        "per-endpoint breakdown, and a daily trend."
    ),
)
def get_request_analytics(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[object, Depends(get_current_admin)],
    days: int = Query(
        default=30, ge=1, le=365, description="Timeframe in days for the report"
    ),
) -> RequestAnalyticsResponse:
    return RequestAnalyticsService.get_request_analytics(db=db, days=days)


@router.get(
    "/requests/export",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
    summary="Export API Request Analytics as CSV",
    description="Admin endpoint returning raw request logs as a CSV file.",
)
def export_request_analytics(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[object, Depends(get_current_admin)],
    days: int = Query(
        default=30, ge=1, le=365, description="Timeframe in days for the export"
    ),
) -> PlainTextResponse:
    csv_data = RequestAnalyticsService.export_csv(db=db, days=days)
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="request-analytics-{days}d.csv"'
        },
    )


@router.get(
    "/profile",
    response_model=ProfileAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get professional profile analytics dashboard data",
)
def get_my_profile_analytics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileAnalyticsResponse:
    return AnalyticsService.get_profile_analytics(db=db, user_id=current_user.id)


@router.post(
    "/profile/click",
    status_code=status.HTTP_200_OK,
    summary="Track a user click (repository or project)",
)
def track_profile_click(
    request: TrackClickRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
):
    AnalyticsService.log_profile_click(
        db=db,
        click_type=request.click_type,
        target_user_id=request.target_user_id,
        entity_id=request.entity_id,
        user_id=current_user.id if current_user else None,
    )
    return {"status": "success"}
