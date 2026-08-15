from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import HTTPException, status
from sqlalchemy import func, select, or_, Integer
from sqlalchemy.orm import Session

from app.middleware.audit_context import (
    audit_ip_address,
    audit_request_method,
    audit_request_path,
    audit_user_agent,
)
from app.models.security_event import (
    SecurityEvent,
    SecurityEventSeverity,
    SecurityEventType,
)
from app.models.user import User
from app.schemas.security_event import (
    PaginatedSecurityEventsResponse,
    SecurityEventResponse,
    SecurityEventSummaryResponse,
    TopOffendingIPItem,
)

logger = structlog.get_logger("devlink.security_events")


class SecurityEventService:
    """
    Business logic for Security Event Monitoring & Alerting (#613).
    """

    # Default severity mapping per event type
    DEFAULT_SEVERITIES = {
        SecurityEventType.FAILED_LOGIN: SecurityEventSeverity.MEDIUM,
        SecurityEventType.PASSWORD_RESET: SecurityEventSeverity.MEDIUM,
        SecurityEventType.EMAIL_CHANGE: SecurityEventSeverity.MEDIUM,
        SecurityEventType.PERMISSION_UPDATE: SecurityEventSeverity.MEDIUM,
        SecurityEventType.SUSPICIOUS_API_USAGE: SecurityEventSeverity.HIGH,
        SecurityEventType.ACCOUNT_LOCKOUT: SecurityEventSeverity.CRITICAL,
    }

    # ------------------------------------------------------------------
    # Alert & Severity Evaluator
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate_alert_rules(
        db: Session,
        event_type: SecurityEventType,
        given_severity: SecurityEventSeverity | None,
        risk_score: float,
        ip_address: str | None,
        actor_id: uuid.UUID | None,
        target_user_id: uuid.UUID | None,
    ) -> tuple[SecurityEventSeverity, bool, str | None]:
        """
        Evaluates risk score and recent event frequency to determine final severity
        and whether an automated security alert should be triggered.
        """
        # Determine base severity
        severity = given_severity or SecurityEventService.DEFAULT_SEVERITIES.get(
            event_type, SecurityEventSeverity.INFO
        )
        alert_triggered = False
        alert_msg: str | None = None

        now = datetime.now(timezone.utc)
        h24_ago = now - timedelta(hours=24)
        m15_ago = now - timedelta(minutes=15)

        # Rule 1: Account Lockout is always a critical security alert
        if event_type == SecurityEventType.ACCOUNT_LOCKOUT:
            severity = SecurityEventSeverity.CRITICAL
            alert_triggered = True
            alert_msg = "Critical Alert: User account locked due to excessive failed attempts or administrative action."

        # Rule 2: Suspicious API Usage
        elif event_type == SecurityEventType.SUSPICIOUS_API_USAGE:
            if risk_score >= 0.7:
                severity = SecurityEventSeverity.CRITICAL
                alert_triggered = True
                alert_msg = f"Critical API Abuse Alert: High risk score ({risk_score:.2f}) detected."
            elif risk_score >= 0.4:
                severity = SecurityEventSeverity.HIGH
                alert_triggered = True
                alert_msg = (
                    f"API Usage Warning: Elevated risk score ({risk_score:.2f})."
                )

        # Rule 3: Failed Login Frequency
        elif event_type == SecurityEventType.FAILED_LOGIN:
            # Check recent failed logins in past 15 mins for same IP or user
            recent_fails = 0
            if ip_address or target_user_id or actor_id:
                stmt = (
                    select(func.count())
                    .select_from(SecurityEvent)
                    .where(
                        SecurityEvent.event_type == SecurityEventType.FAILED_LOGIN,
                        SecurityEvent.created_at >= m15_ago,
                    )
                )
                conditions = []
                if ip_address:
                    conditions.append(SecurityEvent.ip_address == ip_address)
                if target_user_id:
                    conditions.append(SecurityEvent.target_user_id == target_user_id)
                if actor_id:
                    conditions.append(SecurityEvent.actor_id == actor_id)

                if conditions:
                    stmt = stmt.where(or_(*conditions))
                    recent_fails = db.scalar(stmt) or 0

            if recent_fails >= 4 or risk_score >= 0.8:
                severity = SecurityEventSeverity.CRITICAL
                alert_triggered = True
                alert_msg = f"Brute-Force Alert: {recent_fails + 1} failed logins detected in the last 15 minutes."
            elif recent_fails >= 2 or risk_score >= 0.5:
                severity = SecurityEventSeverity.HIGH
                alert_triggered = True
                alert_msg = f"Repeated Login Failures: {recent_fails + 1} failed login attempts recorded."

        # Rule 4: Permission Update / Role Promotion
        elif event_type == SecurityEventType.PERMISSION_UPDATE:
            if risk_score >= 0.6:
                severity = SecurityEventSeverity.HIGH
                alert_triggered = True
                alert_msg = (
                    "Security Warning: Critical permission modification performed."
                )

        # Rule 5: High Risk Score Override
        if not alert_triggered and risk_score >= 0.75:
            severity = SecurityEventSeverity.HIGH
            alert_triggered = True
            alert_msg = f"High Risk Security Alert: Risk score {risk_score:.2f} exceeded alert threshold."

        return severity, alert_triggered, alert_msg

    # ------------------------------------------------------------------
    # Logging Service Method
    # ------------------------------------------------------------------

    @staticmethod
    def log_security_event(
        db: Session,
        *,
        event_type: SecurityEventType,
        description: str,
        actor_id: uuid.UUID | None = None,
        target_user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        risk_score: float = 0.0,
        severity: SecurityEventSeverity | None = None,
        request_method: str | None = None,
        request_path: str | None = None,
        metadata_payload: dict | None = None,
    ) -> SecurityEvent:
        """
        Record a structured, alert-ready security event in DB and logger.
        """
        resolved_ip = ip_address or audit_ip_address.get()
        resolved_ua = user_agent or audit_user_agent.get()
        resolved_method = request_method or audit_request_method.get()
        resolved_path = request_path or audit_request_path.get()

        computed_severity, alert_triggered, alert_message = (
            SecurityEventService._evaluate_alert_rules(
                db=db,
                event_type=event_type,
                given_severity=severity,
                risk_score=risk_score,
                ip_address=resolved_ip,
                actor_id=actor_id,
                target_user_id=target_user_id,
            )
        )

        event = SecurityEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            severity=computed_severity,
            risk_score=risk_score,
            description=description,
            actor_id=actor_id,
            target_user_id=target_user_id,
            ip_address=resolved_ip,
            user_agent=resolved_ua,
            request_method=resolved_method,
            request_path=resolved_path,
            alert_triggered=alert_triggered,
            alert_message=alert_message,
            is_resolved=False,
            metadata_payload=metadata_payload or {},
            created_at=datetime.now(timezone.utc),
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(
            "security_event_logged",
            event_id=str(event.id),
            event_type=event_type.value,
            severity=computed_severity.value,
            alert_triggered=alert_triggered,
            actor_id=str(actor_id) if actor_id else None,
            target_user_id=str(target_user_id) if target_user_id else None,
            ip_address=resolved_ip,
        )

        return event

    # ------------------------------------------------------------------
    # Query & Retrieval Methods
    # ------------------------------------------------------------------

    @staticmethod
    def get_security_event_or_404(db: Session, event_id: uuid.UUID) -> SecurityEvent:
        event = db.get(SecurityEvent, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Security event not found",
            )
        return event

    @staticmethod
    def list_security_events(
        db: Session,
        *,
        event_type: SecurityEventType | None = None,
        severity: SecurityEventSeverity | None = None,
        alert_triggered: bool | None = None,
        is_resolved: bool | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> PaginatedSecurityEventsResponse:
        stmt = select(SecurityEvent)

        if event_type:
            stmt = stmt.where(SecurityEvent.event_type == event_type)
        if severity:
            stmt = stmt.where(SecurityEvent.severity == severity)
        if alert_triggered is not None:
            stmt = stmt.where(SecurityEvent.alert_triggered.is_(alert_triggered))
        if is_resolved is not None:
            stmt = stmt.where(SecurityEvent.is_resolved.is_(is_resolved))
        if start_date:
            stmt = stmt.where(SecurityEvent.created_at >= start_date)
        if end_date:
            stmt = stmt.where(SecurityEvent.created_at <= end_date)
        if user_id:
            stmt = stmt.where(
                or_(
                    SecurityEvent.actor_id == user_id,
                    SecurityEvent.target_user_id == user_id,
                )
            )
        if ip_address:
            stmt = stmt.where(SecurityEvent.ip_address == ip_address)
        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(SecurityEvent.description).like(pattern)
                | func.lower(SecurityEvent.ip_address).like(pattern)
            )

        # Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = db.scalar(count_stmt) or 0

        # Pagination & ordering
        offset = (page - 1) * limit
        paginated_stmt = (
            stmt.order_by(SecurityEvent.created_at.desc()).offset(offset).limit(limit)
        )

        events = list(db.scalars(paginated_stmt).all())
        pages = (total_count + limit - 1) // limit if limit > 0 else 1

        items = [SecurityEventResponse.model_validate(e) for e in events]
        return PaginatedSecurityEventsResponse(
            items=items,
            total=total_count,
            page=page,
            limit=limit,
            pages=pages,
        )

    @staticmethod
    def resolve_security_event(
        db: Session,
        event_id: uuid.UUID,
        resolver_user: User,
        notes: str | None = None,
    ) -> SecurityEvent:
        event = SecurityEventService.get_security_event_or_404(db, event_id)

        event.is_resolved = True
        event.resolved_at = datetime.now(timezone.utc)
        event.resolved_by_id = resolver_user.id
        event.resolution_notes = (
            notes.strip() if notes else "Resolved by security administrator."
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(
            "security_event_resolved",
            event_id=str(event.id),
            resolved_by=str(resolver_user.id),
        )
        return event

    @staticmethod
    def get_summary(db: Session) -> SecurityEventSummaryResponse:
        now = datetime.now(timezone.utc)
        h24_ago = now - timedelta(hours=24)

        total_cnt = db.scalar(select(func.count()).select_from(SecurityEvent)) or 0
        events_24h = (
            db.scalar(
                select(func.count())
                .select_from(SecurityEvent)
                .where(SecurityEvent.created_at >= h24_ago)
            )
            or 0
        )
        alerts_total = (
            db.scalar(
                select(func.count())
                .select_from(SecurityEvent)
                .where(SecurityEvent.alert_triggered.is_(True))
            )
            or 0
        )
        unresolved_cnt = (
            db.scalar(
                select(func.count())
                .select_from(SecurityEvent)
                .where(
                    SecurityEvent.alert_triggered.is_(True),
                    SecurityEvent.is_resolved.is_(False),
                )
            )
            or 0
        )
        critical_24h = (
            db.scalar(
                select(func.count())
                .select_from(SecurityEvent)
                .where(
                    SecurityEvent.created_at >= h24_ago,
                    SecurityEvent.severity == SecurityEventSeverity.CRITICAL,
                )
            )
            or 0
        )

        # Event type breakdown
        type_rows = db.execute(
            select(SecurityEvent.event_type, func.count()).group_by(
                SecurityEvent.event_type
            )
        ).all()
        type_breakdown = {
            t.value if hasattr(t, "value") else str(t): cnt for t, cnt in type_rows
        }

        # Severity breakdown
        sev_rows = db.execute(
            select(SecurityEvent.severity, func.count()).group_by(
                SecurityEvent.severity
            )
        ).all()
        sev_breakdown = {
            s.value if hasattr(s, "value") else str(s): cnt for s, cnt in sev_rows
        }

        # Top offending IPs
        ip_rows = db.execute(
            select(
                SecurityEvent.ip_address,
                func.count().label("total_cnt"),
                func.sum(
                    func.cast(
                        SecurityEvent.severity == SecurityEventSeverity.CRITICAL,
                        Integer,
                    )
                ).label("critical_cnt"),
            )
            .where(SecurityEvent.ip_address.isnot(None))
            .group_by(SecurityEvent.ip_address)
            .order_by(func.count().desc())
            .limit(10)
        ).all()

        top_ips = [
            TopOffendingIPItem(
                ip_address=ip,
                event_count=cnt,
                critical_alerts_count=crit_cnt or 0,
            )
            for ip, cnt, crit_cnt in ip_rows
        ]

        return SecurityEventSummaryResponse(
            total_events=total_cnt,
            events_24h=events_24h,
            alerts_triggered_total=alerts_total,
            unresolved_alerts_count=unresolved_cnt,
            critical_alerts_24h=critical_24h,
            event_type_breakdown=type_breakdown,
            severity_breakdown=sev_breakdown,
            top_offending_ips=top_ips,
        )
