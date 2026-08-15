"""
API Router for Security Event Monitoring & Administrative Review (#613)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_database
from app.models.security_event import SecurityEventSeverity, SecurityEventType
from app.models.user import User
from app.schemas.security_event import (
    PaginatedSecurityEventsResponse,
    SecurityEventCreate,
    SecurityEventResolveRequest,
    SecurityEventResponse,
    SecurityEventSummaryResponse,
)
from app.services.security_event_service import SecurityEventService

router = APIRouter(
    prefix="/admin/security-events",
    tags=["Security Events Monitoring"],
)


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Ensure the caller has system admin privileges."""
    if (
        getattr(current_user, "system_role", None) != "admin"
        and getattr(current_user, "role", None) != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for Security Event Monitoring.",
        )
    return current_user


@router.get(
    "",
    response_model=PaginatedSecurityEventsResponse,
    summary="List and filter security events",
    description="Retrieve paginated security events filtered by event type, severity, alert status, resolution status, date range, user ID, or client IP.",
)
@router.get(
    "/",
    response_model=PaginatedSecurityEventsResponse,
    include_in_schema=False,
)
def list_security_events(
    event_type: Optional[SecurityEventType] = Query(
        None, description="Filter by event classification"
    ),
    severity: Optional[SecurityEventSeverity] = Query(
        None, description="Filter by severity level"
    ),
    alert_triggered: Optional[bool] = Query(
        None, description="Filter by alert triggered status"
    ),
    is_resolved: Optional[bool] = Query(
        None, description="Filter by resolution status"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Filter events from date (ISO 8601)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter events to date (ISO 8601)"
    ),
    user_id: Optional[uuid.UUID] = Query(
        None, description="Filter by actor or target user ID"
    ),
    ip_address: Optional[str] = Query(None, description="Filter by client IP address"),
    search: Optional[str] = Query(
        None, description="Full-text search on description or IP"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> PaginatedSecurityEventsResponse:
    return SecurityEventService.list_security_events(
        db,
        event_type=event_type,
        severity=severity,
        alert_triggered=alert_triggered,
        is_resolved=is_resolved,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        ip_address=ip_address,
        search=search,
        page=page,
        limit=limit,
    )


@router.get(
    "/summary",
    response_model=SecurityEventSummaryResponse,
    summary="Get security monitoring summary and metrics",
    description="Returns aggregate metrics: 24h event volume, critical alerts count, unresolved alerts count, event type breakdown, severity breakdown, and top offending IPs.",
)
def get_security_events_summary(
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> SecurityEventSummaryResponse:
    return SecurityEventService.get_summary(db)


@router.post(
    "/log",
    response_model=SecurityEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a security event",
    description="Manually or programmatically log a critical security event with alert threshold evaluation.",
)
def log_security_event(
    event_in: SecurityEventCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_admin),
) -> SecurityEventResponse:
    event = SecurityEventService.log_security_event(
        db,
        event_type=event_in.event_type,
        description=event_in.description,
        actor_id=event_in.actor_id or current_user.id,
        target_user_id=event_in.target_user_id,
        ip_address=event_in.ip_address,
        user_agent=event_in.user_agent,
        risk_score=event_in.risk_score or 0.0,
        severity=event_in.severity,
        request_method=event_in.request_method,
        request_path=event_in.request_path,
        metadata_payload=event_in.metadata_payload,
    )
    return SecurityEventResponse.model_validate(event)


@router.get(
    "/{event_id}",
    response_model=SecurityEventResponse,
    summary="Get security event details",
)
def get_security_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> SecurityEventResponse:
    event = SecurityEventService.get_security_event_or_404(db, event_id)
    return SecurityEventResponse.model_validate(event)


@router.post(
    "/{event_id}/resolve",
    response_model=SecurityEventResponse,
    summary="Resolve a security event alert",
    description="Mark a security event or alert as resolved with administrator notes.",
)
@router.post(
    "/{event_id}/acknowledge",
    response_model=SecurityEventResponse,
    include_in_schema=False,
)
def resolve_security_event(
    event_id: uuid.UUID,
    payload: Optional[SecurityEventResolveRequest] = None,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_admin),
) -> SecurityEventResponse:
    notes = (
        payload.resolution_notes
        if payload
        else "Acknowledged and resolved by administrator."
    )
    event = SecurityEventService.resolve_security_event(
        db, event_id=event_id, resolver_user=current_user, notes=notes
    )
    return SecurityEventResponse.model_validate(event)
