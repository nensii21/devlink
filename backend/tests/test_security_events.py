"""
Unit & Integration Tests for Security Event Monitoring (#613)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.security_event import (
    SecurityEvent,
    SecurityEventSeverity,
    SecurityEventType,
)
from app.models.user import User
from app.schemas.security_event import (
    SecurityEventSummaryResponse,
)
from app.services.security_event_service import SecurityEventService

# ---------------------------------------------------------------------------
# Test Fixtures / Mock Helpers
# ---------------------------------------------------------------------------


def _make_mock_user(
    username: str = "secadmin", system_role: str = "admin"
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = username
    user.first_name = "Security"
    user.last_name = "Admin"
    user.system_role = system_role
    user.role = system_role
    return user


def _make_mock_security_event(
    event_type: SecurityEventType = SecurityEventType.FAILED_LOGIN,
    severity: SecurityEventSeverity = SecurityEventSeverity.MEDIUM,
    risk_score: float = 0.2,
    alert_triggered: bool = False,
    is_resolved: bool = False,
    ip_address: str = "192.168.1.100",
) -> MagicMock:
    event = MagicMock(spec=SecurityEvent)
    event.id = uuid.uuid4()
    event.event_type = event_type
    event.severity = severity
    event.risk_score = risk_score
    event.description = f"Test security event: {event_type.value}"
    event.actor_id = uuid.uuid4()
    event.target_user_id = uuid.uuid4()
    event.ip_address = ip_address
    event.user_agent = "Mozilla/5.0"
    event.request_method = "POST"
    event.request_path = "/api/v1/auth/login"
    event.alert_triggered = alert_triggered
    event.alert_message = "Alert triggered" if alert_triggered else None
    event.is_resolved = is_resolved
    event.resolved_at = datetime.now(timezone.utc) if is_resolved else None
    event.resolved_by_id = uuid.uuid4() if is_resolved else None
    event.resolution_notes = "Resolved" if is_resolved else None
    event.metadata_payload = {"test": True}
    event.created_at = datetime.now(timezone.utc)
    return event


# ---------------------------------------------------------------------------
# 1. Alert & Threshold Evaluation Tests
# ---------------------------------------------------------------------------


class TestSecurityEventAlertRules:
    def test_account_lockout_triggers_critical_alert(self):
        db = MagicMock(spec=Session)
        db.scalar.return_value = 0

        sev, alert, msg = SecurityEventService._evaluate_alert_rules(
            db,
            event_type=SecurityEventType.ACCOUNT_LOCKOUT,
            given_severity=None,
            risk_score=0.5,
            ip_address="10.0.0.1",
            actor_id=None,
            target_user_id=uuid.uuid4(),
        )

        assert sev == SecurityEventSeverity.CRITICAL
        assert alert is True
        assert "account locked" in msg.lower()

    def test_suspicious_api_usage_triggers_high_risk_alert(self):
        db = MagicMock(spec=Session)

        sev, alert, msg = SecurityEventService._evaluate_alert_rules(
            db,
            event_type=SecurityEventType.SUSPICIOUS_API_USAGE,
            given_severity=None,
            risk_score=0.8,
            ip_address="192.168.1.50",
            actor_id=uuid.uuid4(),
            target_user_id=None,
        )

        assert sev == SecurityEventSeverity.CRITICAL
        assert alert is True
        assert "critical api abuse" in msg.lower()

    def test_repeated_failed_logins_triggers_brute_force_alert(self):
        db = MagicMock(spec=Session)
        # Mock 5 recent failed logins
        db.scalar.return_value = 5

        sev, alert, msg = SecurityEventService._evaluate_alert_rules(
            db,
            event_type=SecurityEventType.FAILED_LOGIN,
            given_severity=None,
            risk_score=0.3,
            ip_address="1.2.3.4",
            actor_id=None,
            target_user_id=uuid.uuid4(),
        )

        assert sev == SecurityEventSeverity.CRITICAL
        assert alert is True
        assert "brute-force" in msg.lower()


# ---------------------------------------------------------------------------
# 2. Logging Service Tests (All 6 Monitor Event Types)
# ---------------------------------------------------------------------------


class TestSecurityEventLogging:
    @pytest.mark.parametrize(
        "event_type",
        [
            SecurityEventType.FAILED_LOGIN,
            SecurityEventType.PASSWORD_RESET,
            SecurityEventType.EMAIL_CHANGE,
            SecurityEventType.PERMISSION_UPDATE,
            SecurityEventType.SUSPICIOUS_API_USAGE,
            SecurityEventType.ACCOUNT_LOCKOUT,
        ],
    )
    def test_log_security_event_all_monitored_types(self, event_type):
        db = MagicMock(spec=Session)
        db.scalar.return_value = 0

        actor_id = uuid.uuid4()
        event = SecurityEventService.log_security_event(
            db,
            event_type=event_type,
            description=f"Testing monitored security event: {event_type.value}",
            actor_id=actor_id,
            ip_address="127.0.0.1",
            risk_score=0.4,
        )

        assert event.event_type == event_type
        assert event.actor_id == actor_id
        db.add.assert_called_once()
        db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# 3. Query, Filtering & Resolution Tests
# ---------------------------------------------------------------------------


class TestSecurityEventQueryAndResolution:
    def test_get_security_event_or_404_found(self):
        db = MagicMock(spec=Session)
        event = _make_mock_security_event()
        db.get.return_value = event

        res = SecurityEventService.get_security_event_or_404(db, event.id)
        assert res == event

    def test_get_security_event_or_404_not_found(self):
        db = MagicMock(spec=Session)
        db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            SecurityEventService.get_security_event_or_404(db, uuid.uuid4())
        assert exc_info.value.status_code == 404

    def test_resolve_security_event_success(self):
        db = MagicMock(spec=Session)
        admin = _make_mock_user()
        event = _make_mock_security_event(alert_triggered=True, is_resolved=False)
        db.get.return_value = event

        resolved = SecurityEventService.resolve_security_event(
            db,
            event_id=event.id,
            resolver_user=admin,
            notes="IP investigated and blocked.",
        )

        assert resolved.is_resolved is True
        assert resolved.resolved_by_id == admin.id
        assert resolved.resolution_notes == "IP investigated and blocked."
        db.commit.assert_called_once()

    def test_get_summary_metrics(self):
        db = MagicMock(spec=Session)
        db.scalar.side_effect = [100, 25, 10, 3, 2]
        db.execute.return_value.all.side_effect = [
            [
                (SecurityEventType.FAILED_LOGIN, 60),
                (SecurityEventType.ACCOUNT_LOCKOUT, 40),
            ],  # type breakdown
            [
                (SecurityEventSeverity.MEDIUM, 70),
                (SecurityEventSeverity.CRITICAL, 30),
            ],  # severity breakdown
            [("1.2.3.4", 15, 5)],  # top IPs
        ]

        summary = SecurityEventService.get_summary(db)

        assert isinstance(summary, SecurityEventSummaryResponse)
        assert summary.total_events == 100
        assert summary.events_24h == 25
        assert summary.alerts_triggered_total == 10
        assert summary.unresolved_alerts_count == 3
        assert len(summary.top_offending_ips) == 1
        assert summary.top_offending_ips[0].ip_address == "1.2.3.4"


# ---------------------------------------------------------------------------
# 4. Admin RBAC Guard Tests
# ---------------------------------------------------------------------------


class TestSecurityEventAdminGuard:
    def test_admin_role_allowed(self):
        from app.routers.security_events import require_admin

        admin = _make_mock_user(system_role="admin")
        assert require_admin(current_user=admin) == admin

    def test_non_admin_forbidden(self):
        from app.routers.security_events import require_admin

        user = _make_mock_user(system_role="user")
        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=user)
        assert exc_info.value.status_code == 403
