"""
Security Audit Dashboard API Router (Issue #622)
================================================

All endpoints are restricted to users with system_role == "admin".
Non-admin users receive HTTP 403.

Endpoint map
────────────
GET  /api/v1/admin/security/summary             Dashboard overview
GET  /api/v1/admin/security/failed-logins       Failed login attempts
GET  /api/v1/admin/security/failed-logins/export  CSV export
GET  /api/v1/admin/security/blocked-ips         Blocked / suspicious IPs
GET  /api/v1/admin/security/suspicious-sessions Suspicious session events
GET  /api/v1/admin/security/suspicious-sessions/export
GET  /api/v1/admin/security/password-resets     Password reset events
GET  /api/v1/admin/security/password-resets/export
GET  /api/v1/admin/security/api-abuse           API abuse reports
GET  /api/v1/admin/security/api-abuse/export
GET  /api/v1/admin/security/alerts              Security alerts
GET  /api/v1/admin/security/alerts/export
GET  /api/v1/admin/security/search              Universal search
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_database
from app.models.user import User
from app.schemas.security_dashboard import (
    BlockedIPEntry,
    PaginatedSecurityLogs,
    SecurityDashboardSummary,
)
from app.services.security_dashboard_service import SecurityDashboardService

router = APIRouter(
    prefix="/admin/security",
    tags=["Security Audit Dashboard"],
)


# ---------------------------------------------------------------------------
# Role guard dependency
# ---------------------------------------------------------------------------


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Ensure the caller has admin privileges."""
    if (
        getattr(current_user, "system_role", None) != "admin"
        and getattr(current_user, "role", None) != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for the Security Audit Dashboard.",
        )
    return current_user


# ---------------------------------------------------------------------------
# Common query params (DRY reuse)
# ---------------------------------------------------------------------------


def _date_params(
    start_date: Optional[datetime] = Query(
        None, description="Filter from this date (ISO 8601)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter to this date (ISO 8601)"
    ),
):
    return start_date, end_date


# ---------------------------------------------------------------------------
# 1.  Dashboard Overview / Summary
# ---------------------------------------------------------------------------


@router.get(
    "/summary",
    response_model=SecurityDashboardSummary,
    summary="Security dashboard overview",
    description=(
        "Returns aggregated counters for the last 24 h / 7 days: "
        "failed logins, suspicious sessions, password resets, API abuse events, "
        "security alerts, and the list of blocked IPs."
    ),
)
def get_dashboard_summary(
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> SecurityDashboardSummary:
    return SecurityDashboardService.get_summary(db)


# ---------------------------------------------------------------------------
# 2.  Failed Login Attempts
# ---------------------------------------------------------------------------


@router.get(
    "/failed-logins",
    response_model=PaginatedSecurityLogs,
    summary="Failed login attempts",
    description="Paginated list of all failed login events with filtering and search.",
)
def get_failed_logins(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    ip_address: Optional[str] = Query(None, description="Filter by exact IP address"),
    actor_id: Optional[uuid.UUID] = Query(None, description="Filter by actor user ID"),
    search: Optional[str] = Query(
        None, description="Full-text search on description/IP/entity"
    ),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> PaginatedSecurityLogs:
    return SecurityDashboardService.get_failed_logins(
        db,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        ip_address=ip_address,
        actor_id=actor_id,
        search=search,
    )


@router.get(
    "/failed-logins/export",
    summary="Export failed login attempts as CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_failed_logins(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    ip_address: Optional[str] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> Response:
    csv_data = SecurityDashboardService.export_failed_logins_csv(
        db, start_date=start_date, end_date=end_date, ip_address=ip_address
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="failed_logins.csv"'},
    )


# ---------------------------------------------------------------------------
# 3.  Blocked IPs
# ---------------------------------------------------------------------------


@router.get(
    "/blocked-ips",
    response_model=list[BlockedIPEntry],
    summary="Blocked / suspicious IP addresses",
    description=(
        "Returns IP addresses that have generated ≥ `threshold` failed login "
        "events, along with event counts and associated user IDs."
    ),
)
def get_blocked_ips(
    threshold: int = Query(
        5, ge=1, description="Minimum failed login count to consider IP blocked"
    ),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> list[BlockedIPEntry]:
    return SecurityDashboardService.get_blocked_ips(
        db, threshold=threshold, start_date=start_date, end_date=end_date
    )


# ---------------------------------------------------------------------------
# 4.  Suspicious Sessions
# ---------------------------------------------------------------------------


@router.get(
    "/suspicious-sessions",
    response_model=PaginatedSecurityLogs,
    summary="Suspicious session events",
    description="Paginated list of suspicious login attempt events.",
)
def get_suspicious_sessions(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    ip_address: Optional[str] = Query(None),
    actor_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> PaginatedSecurityLogs:
    return SecurityDashboardService.get_suspicious_sessions(
        db,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        ip_address=ip_address,
        actor_id=actor_id,
        search=search,
    )


@router.get(
    "/suspicious-sessions/export",
    summary="Export suspicious sessions as CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_suspicious_sessions(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> Response:
    csv_data = SecurityDashboardService.export_suspicious_sessions_csv(
        db, start_date=start_date, end_date=end_date
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="suspicious_sessions.csv"'
        },
    )


# ---------------------------------------------------------------------------
# 5.  Password Resets
# ---------------------------------------------------------------------------


@router.get(
    "/password-resets",
    response_model=PaginatedSecurityLogs,
    summary="Password reset events",
    description="Paginated list of all password reset audit events.",
)
def get_password_resets(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    actor_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> PaginatedSecurityLogs:
    return SecurityDashboardService.get_password_resets(
        db,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        actor_id=actor_id,
        search=search,
    )


@router.get(
    "/password-resets/export",
    summary="Export password reset events as CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_password_resets(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> Response:
    csv_data = SecurityDashboardService.export_password_resets_csv(
        db, start_date=start_date, end_date=end_date
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="password_resets.csv"'},
    )


# ---------------------------------------------------------------------------
# 6.  API Abuse Reports
# ---------------------------------------------------------------------------


@router.get(
    "/api-abuse",
    response_model=PaginatedSecurityLogs,
    summary="API abuse reports",
    description="Paginated list of failed API access events (potential abuse / scraping).",
)
def get_api_abuse(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    ip_address: Optional[str] = Query(None),
    actor_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> PaginatedSecurityLogs:
    return SecurityDashboardService.get_api_abuse(
        db,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        ip_address=ip_address,
        actor_id=actor_id,
        search=search,
    )


@router.get(
    "/api-abuse/export",
    summary="Export API abuse reports as CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_api_abuse(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> Response:
    csv_data = SecurityDashboardService.export_api_abuse_csv(
        db, start_date=start_date, end_date=end_date
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="api_abuse.csv"'},
    )


# ---------------------------------------------------------------------------
# 7.  Security Alerts
# ---------------------------------------------------------------------------


@router.get(
    "/alerts",
    summary="Security alerts",
    description=(
        "Returns high-severity security events (suspicious logins, token revocations, "
        "bans, suspensions) with a computed severity label. "
        "Filter by severity: 'critical', 'high', or 'medium'."
    ),
)
def get_security_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    severity: Optional[str] = Query(
        None, description="Filter by severity: critical | high | medium"
    ),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    return SecurityDashboardService.get_security_alerts(
        db,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        severity=severity,
        search=search,
    )


@router.get(
    "/alerts/export",
    summary="Export security alerts as CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_security_alerts(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> Response:
    csv_data = SecurityDashboardService.export_security_alerts_csv(
        db, start_date=start_date, end_date=end_date
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="security_alerts.csv"'},
    )


# ---------------------------------------------------------------------------
# 8.  Universal Search
# ---------------------------------------------------------------------------


@router.get(
    "/search",
    response_model=PaginatedSecurityLogs,
    summary="Search all security events",
    description=(
        "Full-text search across all security-relevant audit logs "
        "(description, IP address, entity ID). "
        "Covers failed logins, suspicious sessions, alerts, and password resets."
    ),
)
def search_security_events(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> PaginatedSecurityLogs:
    return SecurityDashboardService.search_all(
        db,
        q=q,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )
