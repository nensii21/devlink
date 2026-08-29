"""
Security Audit Dashboard Service (Issue #622)
=============================================

Provides admin-only analytics and query capabilities over the existing
AuditLog table for the Security Audit Dashboard.

Dashboard Sections covered
──────────────────────────
1.  Failed login attempts  (action = FAILED_LOGIN)
2.  Blocked IPs            (IPs with ≥ N failed logins)
3.  Suspicious sessions    (action = SUSPICIOUS_LOGIN_ATTEMPT)
4.  Password resets        (action = PASSWORD_RESET)
5.  API abuse reports      (action = API_ACCESS with success=False, or rate-limit events)
6.  Security alerts        (critical events: suspicious login + failed login + token revoke)

All query methods support:
  - date range filtering  (start_date / end_date)
  - IP address filtering
  - actor / user search   (actor_id or free-text search on description)
  - pagination            (page + limit)
  - CSV export
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditLog
from app.schemas.security_dashboard import (
    BlockedIPEntry,
    PaginatedSecurityLogs,
    SecurityAuditLogItem,
    SecurityAlertItem,
    SecurityDashboardSummary,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FAILED_LOGIN_ACTIONS = {AuditAction.FAILED_LOGIN}
SUSPICIOUS_ACTIONS = {AuditAction.SUSPICIOUS_LOGIN_ATTEMPT}
PASSWORD_RESET_ACTIONS = {AuditAction.PASSWORD_RESET}
API_ABUSE_ACTIONS = {AuditAction.API_ACCESS}
TOKEN_REVOKE_ACTIONS = {AuditAction.TOKEN_REVOKED, AuditAction.API_TOKEN_REVOKED}

#: Minimum failed logins from a single IP to be considered "blocked"
BLOCKED_IP_THRESHOLD = 5

#: Security alert actions (high-severity events)
ALERT_ACTIONS = {
    AuditAction.FAILED_LOGIN,
    AuditAction.SUSPICIOUS_LOGIN_ATTEMPT,
    AuditAction.TOKEN_REVOKED,
    AuditAction.USER_BANNED,
    AuditAction.USER_SUSPENDED,
}

SEVERITY_MAP: dict[AuditAction, str] = {
    AuditAction.SUSPICIOUS_LOGIN_ATTEMPT: "critical",
    AuditAction.USER_BANNED: "critical",
    AuditAction.USER_SUSPENDED: "high",
    AuditAction.TOKEN_REVOKED: "high",
    AuditAction.FAILED_LOGIN: "medium",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _apply_common_filters(
    stmt,
    *,
    start_date: datetime | None,
    end_date: datetime | None,
    ip_address: str | None,
    actor_id: uuid.UUID | None,
    search: str | None,
):
    """Apply shared filter clauses to any AuditLog select statement."""
    if start_date:
        stmt = stmt.where(AuditLog.created_at >= start_date)
    if end_date:
        stmt = stmt.where(AuditLog.created_at <= end_date)
    if ip_address:
        stmt = stmt.where(AuditLog.ip_address == ip_address)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(AuditLog.description).like(pattern)
            | func.lower(AuditLog.ip_address).like(pattern)
            | func.lower(AuditLog.entity_id).like(pattern)
        )
    return stmt


def _paginate(stmt, *, page: int, limit: int, db: Session) -> dict[str, Any]:
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0
    offset = (page - 1) * limit
    rows = list(
        db.scalars(
            stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        )
    )
    pages = (total + limit - 1) // limit if limit > 0 else 1
    return {"items": rows, "total": total, "page": page, "limit": limit, "pages": pages}


def _to_item(log: AuditLog) -> SecurityAuditLogItem:
    return SecurityAuditLogItem(
        id=log.id,
        actor_id=log.actor_id,
        target_user_id=log.target_user_id,
        project_id=log.project_id,
        organization_id=log.organization_id,
        action=log.action.value if hasattr(log.action, "value") else str(log.action),
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        description=log.description,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        request_method=log.request_method,
        request_path=log.request_path,
        success=log.success,
        status_code=log.status_code,
        error_message=log.error_message,
        metadata_info=log.metadata_info,
        created_at=log.created_at,
    )


def _export_csv(logs: list[AuditLog]) -> str:
    """Serialise a list of AuditLog rows to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "Timestamp",
            "Action",
            "Actor ID",
            "Target User ID",
            "Entity Type",
            "Entity ID",
            "Description",
            "IP Address",
            "User Agent",
            "Request Method",
            "Request Path",
            "Success",
            "Status Code",
            "Error Message",
        ]
    )
    for log in logs:
        action_str = (
            log.action.value if hasattr(log.action, "value") else str(log.action)
        )
        writer.writerow(
            [
                str(log.id),
                log.created_at.isoformat() if log.created_at else "",
                action_str,
                str(log.actor_id) if log.actor_id else "",
                str(log.target_user_id) if log.target_user_id else "",
                log.entity_type or "",
                str(log.entity_id) if log.entity_id else "",
                log.description or "",
                log.ip_address or "",
                (log.user_agent or "")[:200],
                log.request_method or "",
                log.request_path or "",
                str(log.success),
                str(log.status_code) if log.status_code is not None else "",
                log.error_message or "",
            ]
        )
    return output.getvalue()


# ---------------------------------------------------------------------------
# SecurityDashboardService
# ---------------------------------------------------------------------------


class SecurityDashboardService:
    """
    Admin-only service powering the Security Audit Dashboard.
    All methods require the caller to be an admin (enforced in the router).
    """

    # ------------------------------------------------------------------ #
    # 1.  Dashboard Overview / Summary                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_summary(db: Session) -> SecurityDashboardSummary:
        """
        Return aggregated counters for the dashboard overview panel.
        Covers the last 24 h and 7 days windows.
        """
        now = _now_utc()
        h24 = now - timedelta(hours=24)
        d7 = now - timedelta(days=7)

        def _count(actions: set[AuditAction], since: datetime) -> int:
            stmt = (
                select(func.count())
                .select_from(AuditLog)
                .where(AuditLog.action.in_(actions))
                .where(AuditLog.created_at >= since)
            )
            return db.scalar(stmt) or 0

        failed_24h = _count(FAILED_LOGIN_ACTIONS, h24)
        failed_7d = _count(FAILED_LOGIN_ACTIONS, d7)
        suspicious_24h = _count(SUSPICIOUS_ACTIONS, h24)
        resets_24h = _count(PASSWORD_RESET_ACTIONS, h24)
        api_abuse_24h = _count(API_ABUSE_ACTIONS, h24)
        alerts_24h = _count(ALERT_ACTIONS, h24)

        # Blocked IPs: IPs with >= BLOCKED_IP_THRESHOLD failed logins ever
        ip_stmt = (
            select(AuditLog.ip_address, func.count().label("cnt"))
            .where(AuditLog.action.in_(FAILED_LOGIN_ACTIONS))
            .where(AuditLog.ip_address.isnot(None))
            .group_by(AuditLog.ip_address)
            .having(func.count() >= BLOCKED_IP_THRESHOLD)
            .order_by(func.count().desc())
        )
        ip_rows = db.execute(ip_stmt).all()
        blocked_ips = [row[0] for row in ip_rows]
        top_threat_ips = [{"ip": row[0], "count": row[1]} for row in ip_rows[:10]]

        return SecurityDashboardSummary(
            failed_logins_24h=failed_24h,
            failed_logins_7d=failed_7d,
            suspicious_sessions_24h=suspicious_24h,
            password_resets_24h=resets_24h,
            api_abuse_events_24h=api_abuse_24h,
            total_security_alerts_24h=alerts_24h,
            blocked_ips=blocked_ips,
            top_threat_ips=top_threat_ips,
        )

    # ------------------------------------------------------------------ #
    # 2.  Failed Login Attempts                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_failed_logins(
        db: Session,
        *,
        page: int = 1,
        limit: int = 50,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        ip_address: str | None = None,
        actor_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> PaginatedSecurityLogs:
        stmt = select(AuditLog).where(AuditLog.action.in_(FAILED_LOGIN_ACTIONS))
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=ip_address,
            actor_id=actor_id,
            search=search,
        )
        result = _paginate(stmt, page=page, limit=limit, db=db)
        return PaginatedSecurityLogs(
            items=[_to_item(r) for r in result["items"]],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"],
        )

    @staticmethod
    def export_failed_logins_csv(
        db: Session,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        ip_address: str | None = None,
    ) -> str:
        stmt = select(AuditLog).where(AuditLog.action.in_(FAILED_LOGIN_ACTIONS))
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=ip_address,
            actor_id=None,
            search=None,
        )
        logs = list(db.scalars(stmt.order_by(AuditLog.created_at.desc()).limit(10000)))
        return _export_csv(logs)

    # ------------------------------------------------------------------ #
    # 3.  Blocked IPs                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_blocked_ips(
        db: Session,
        *,
        threshold: int = BLOCKED_IP_THRESHOLD,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[BlockedIPEntry]:
        """
        Return IPs that have accumulated >= `threshold` failed login events.
        """
        stmt = (
            select(AuditLog.ip_address, func.count().label("cnt"))
            .where(AuditLog.action.in_(FAILED_LOGIN_ACTIONS))
            .where(AuditLog.ip_address.isnot(None))
        )
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
        stmt = (
            stmt.group_by(AuditLog.ip_address)
            .having(func.count() >= threshold)
            .order_by(func.count().desc())
        )
        rows = db.execute(stmt).all()

        result: list[BlockedIPEntry] = []
        for ip, cnt in rows:
            # Last seen timestamp for this IP
            last_stmt = (
                select(AuditLog.created_at)
                .where(AuditLog.ip_address == ip)
                .where(AuditLog.action.in_(FAILED_LOGIN_ACTIONS))
                .order_by(AuditLog.created_at.desc())
                .limit(1)
            )
            last_seen = db.scalar(last_stmt)

            # Distinct user ids hit from this IP
            user_stmt = (
                select(AuditLog.actor_id)
                .where(AuditLog.ip_address == ip)
                .where(AuditLog.action.in_(FAILED_LOGIN_ACTIONS))
                .where(AuditLog.actor_id.isnot(None))
                .distinct()
            )
            user_ids = [str(r) for r in db.scalars(user_stmt).all()]

            result.append(
                BlockedIPEntry(
                    ip_address=ip,
                    failed_login_count=cnt,
                    last_seen=last_seen,
                    associated_user_ids=user_ids,
                )
            )
        return result

    # ------------------------------------------------------------------ #
    # 4.  Suspicious Sessions                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_suspicious_sessions(
        db: Session,
        *,
        page: int = 1,
        limit: int = 50,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        ip_address: str | None = None,
        actor_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> PaginatedSecurityLogs:
        stmt = select(AuditLog).where(AuditLog.action.in_(SUSPICIOUS_ACTIONS))
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=ip_address,
            actor_id=actor_id,
            search=search,
        )
        result = _paginate(stmt, page=page, limit=limit, db=db)
        return PaginatedSecurityLogs(
            items=[_to_item(r) for r in result["items"]],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"],
        )

    @staticmethod
    def export_suspicious_sessions_csv(
        db: Session,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
        stmt = select(AuditLog).where(AuditLog.action.in_(SUSPICIOUS_ACTIONS))
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=None,
            actor_id=None,
            search=None,
        )
        logs = list(db.scalars(stmt.order_by(AuditLog.created_at.desc()).limit(10000)))
        return _export_csv(logs)

    # ------------------------------------------------------------------ #
    # 5.  Password Resets                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_password_resets(
        db: Session,
        *,
        page: int = 1,
        limit: int = 50,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        actor_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> PaginatedSecurityLogs:
        stmt = select(AuditLog).where(AuditLog.action.in_(PASSWORD_RESET_ACTIONS))
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=None,
            actor_id=actor_id,
            search=search,
        )
        result = _paginate(stmt, page=page, limit=limit, db=db)
        return PaginatedSecurityLogs(
            items=[_to_item(r) for r in result["items"]],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"],
        )

    @staticmethod
    def export_password_resets_csv(
        db: Session,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
        stmt = select(AuditLog).where(AuditLog.action.in_(PASSWORD_RESET_ACTIONS))
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=None,
            actor_id=None,
            search=None,
        )
        logs = list(db.scalars(stmt.order_by(AuditLog.created_at.desc()).limit(10000)))
        return _export_csv(logs)

    # ------------------------------------------------------------------ #
    # 6.  API Abuse Reports                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_api_abuse(
        db: Session,
        *,
        page: int = 1,
        limit: int = 50,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        ip_address: str | None = None,
        actor_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> PaginatedSecurityLogs:
        stmt = (
            select(AuditLog)
            .where(AuditLog.action.in_(API_ABUSE_ACTIONS))
            .where(AuditLog.success.is_(False))
        )
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=ip_address,
            actor_id=actor_id,
            search=search,
        )
        result = _paginate(stmt, page=page, limit=limit, db=db)
        return PaginatedSecurityLogs(
            items=[_to_item(r) for r in result["items"]],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"],
        )

    @staticmethod
    def export_api_abuse_csv(
        db: Session,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
        stmt = (
            select(AuditLog)
            .where(AuditLog.action.in_(API_ABUSE_ACTIONS))
            .where(AuditLog.success.is_(False))
        )
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=None,
            actor_id=None,
            search=None,
        )
        logs = list(db.scalars(stmt.order_by(AuditLog.created_at.desc()).limit(10000)))
        return _export_csv(logs)

    # ------------------------------------------------------------------ #
    # 7.  Security Alerts                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_security_alerts(
        db: Session,
        *,
        page: int = 1,
        limit: int = 50,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        severity: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """
        Return high-severity security events with a computed severity label.
        Optionally filter by severity ('critical', 'high', 'medium').
        """
        target_actions = set(ALERT_ACTIONS)
        if severity:
            target_actions = {a for a, s in SEVERITY_MAP.items() if s == severity}

        stmt = select(AuditLog).where(AuditLog.action.in_(target_actions))
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=None,
            actor_id=None,
            search=search,
        )
        result = _paginate(stmt, page=page, limit=limit, db=db)

        items = [
            SecurityAlertItem(
                id=log.id,
                action=(
                    log.action.value
                    if hasattr(log.action, "value")
                    else str(log.action)
                ),
                description=log.description,
                ip_address=log.ip_address,
                actor_id=log.actor_id,
                created_at=log.created_at,
                severity=SEVERITY_MAP.get(log.action, "medium"),
            )
            for log in result["items"]
        ]

        return {
            "items": items,
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"],
            "pages": result["pages"],
        }

    @staticmethod
    def export_security_alerts_csv(
        db: Session,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
        stmt = select(AuditLog).where(AuditLog.action.in_(ALERT_ACTIONS))
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=None,
            actor_id=None,
            search=None,
        )
        logs = list(db.scalars(stmt.order_by(AuditLog.created_at.desc()).limit(10000)))
        return _export_csv(logs)

    # ------------------------------------------------------------------ #
    # 8.  Universal Search across all security events                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def search_all(
        db: Session,
        *,
        q: str,
        page: int = 1,
        limit: int = 50,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> PaginatedSecurityLogs:
        """Full-text search across all security-relevant audit log fields."""
        stmt = select(AuditLog).where(
            AuditLog.action.in_(
                ALERT_ACTIONS
                | FAILED_LOGIN_ACTIONS
                | SUSPICIOUS_ACTIONS
                | PASSWORD_RESET_ACTIONS
            )
        )
        stmt = _apply_common_filters(
            stmt,
            start_date=start_date,
            end_date=end_date,
            ip_address=None,
            actor_id=None,
            search=q,
        )
        result = _paginate(stmt, page=page, limit=limit, db=db)
        return PaginatedSecurityLogs(
            items=[_to_item(r) for r in result["items"]],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"],
        )
