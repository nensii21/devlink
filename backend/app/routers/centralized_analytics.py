from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_optional_current_user
from app.models.user import User
from app.schemas.centralized_analytics import (
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    AnalyticsMetricsSummary,
)
from app.services.centralized_analytics_service import CentralizedAnalyticsService

router = APIRouter(
    prefix="/centralized-analytics",
    tags=["Centralized Analytics"],
)


@router.post(
    "/track",
    response_model=AnalyticsEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Track a application metric event",
)
def track_event(
    payload: AnalyticsEventCreate,
    request: Request,
    db: Session = Depends(get_database),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    user_id = current_user.id if current_user else None

    return CentralizedAnalyticsService.track_event(
        db=db,
        event_type=payload.event_type,
        user_id=user_id,
        properties=payload.properties,
        session_id=payload.session_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.get(
    "/metrics",
    response_model=AnalyticsMetricsSummary,
    summary="Get aggregated application metrics",
)
def get_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_database),
):
    return CentralizedAnalyticsService.get_metrics(db=db, days=days)


@router.get(
    "/events",
    response_model=List[AnalyticsEventResponse],
    summary="List recent centralized analytics events",
)
def list_events(
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_database),
):
    return CentralizedAnalyticsService.list_events(
        db=db, limit=limit, event_type=event_type
    )
