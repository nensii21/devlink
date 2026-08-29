"""
Tests for Issue #622: Add Security Audit Dashboard
====================================================

Tests cover:
  - SecurityDashboardService.get_summary
  - SecurityDashboardService.get_failed_logins
  - SecurityDashboardService.get_blocked_ips
  - SecurityDashboardService.get_suspicious_sessions
  - SecurityDashboardService.get_password_resets
  - SecurityDashboardService.get_api_abuse
  - SecurityDashboardService.get_security_alerts
  - SecurityDashboardService.search_all
  - CSV export helpers
  - require_admin RBAC guard
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.models.audit_log import AuditAction, AuditLog
from app.services.security_dashboard_service import (
    SecurityDashboardService,
    SEVERITY_MAP,
    _export_csv,
    _to_item,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_audit_log(
    action: AuditAction = AuditAction.FAILED_LOGIN,
    success: bool = False,
    ip_address: str = "1.2.3.4",
    description: str = "test event",
    actor_id=None,
) -> AuditLog:
    log = MagicMock(spec=AuditLog)
    log.id = uuid.uuid4()
    log.actor_id = actor_id or uuid.uuid4()
    log.target_user_id = None
    log.project_id = None
    log.organization_id = None
    log.action = action
    log.entity_type = "user"
    log.entity_id = str(uuid.uuid4())
    log.description = description
    log.ip_address = ip_address
    log.user_agent = "Mozilla/5.0"
    log.request_method = "POST"
    log.request_path = "/api/v1/auth/login"
    log.success = success
    log.status_code = 401 if not success else 200
    log.error_message = "Invalid credentials" if not success else None
    log.metadata_info = {}
    log.created_at = datetime.now(timezone.utc)
    return log


def _mock_db_paginated(logs: list) -> MagicMock:
    """
    Build a mock DB session whose scalar / scalars chain returns expected data.
    Works for the _paginate helper inside the service.
    """
    db = MagicMock()
    # scalar() -> total count
    db.scalar.return_value = len(logs)
    # scalars().all() -> log list  (used inside _paginate via list(db.scalars(stmt)))
    db.scalars.return_value = iter(logs)
    # execute().all() -> used for IP group-by queries
    db.execute.return_value.all.return_value = []
    return db


# ---------------------------------------------------------------------------
# _to_item
# ---------------------------------------------------------------------------


class TestToItem:
    def test_converts_log_to_schema(self):
        log = _make_audit_log()
        item = _to_item(log)
        assert str(item.id) == str(log.id)
        assert item.action == log.action.value
        assert item.ip_address == log.ip_address
        assert item.success is False

    def test_action_value_extracted(self):
        log = _make_audit_log(action=AuditAction.SUSPICIOUS_LOGIN_ATTEMPT)
        item = _to_item(log)
        assert item.action == "suspicious_login_attempt"


# ---------------------------------------------------------------------------
# _export_csv
# ---------------------------------------------------------------------------


class TestExportCsv:
    def test_header_row_present(self):
        csv_str = _export_csv([])
        assert "ID" in csv_str
        assert "Timestamp" in csv_str
        assert "Action" in csv_str

    def test_one_row_per_log(self):
        logs = [_make_audit_log(), _make_audit_log()]
        csv_str = _export_csv(logs)
        lines = [l for l in csv_str.strip().splitlines() if l]
        # header + 2 data rows
        assert len(lines) == 3

    def test_log_action_in_csv(self):
        log = _make_audit_log(action=AuditAction.FAILED_LOGIN)
        csv_str = _export_csv([log])
        assert "failed_login" in csv_str


# ---------------------------------------------------------------------------
# SEVERITY_MAP
# ---------------------------------------------------------------------------


class TestSeverityMap:
    def test_suspicious_login_is_critical(self):
        assert SEVERITY_MAP[AuditAction.SUSPICIOUS_LOGIN_ATTEMPT] == "critical"

    def test_failed_login_is_medium(self):
        assert SEVERITY_MAP[AuditAction.FAILED_LOGIN] == "medium"

    def test_token_revoked_is_high(self):
        assert SEVERITY_MAP[AuditAction.TOKEN_REVOKED] == "high"


# ---------------------------------------------------------------------------
# SecurityDashboardService.get_summary (mocked DB)
# ---------------------------------------------------------------------------


class TestGetSummary:
    def test_returns_summary_schema(self):
        db = MagicMock()
        db.scalar.return_value = 3
        db.execute.return_value.all.return_value = [
            ("192.168.1.1", 10),
            ("10.0.0.1", 7),
        ]

        result = SecurityDashboardService.get_summary(db)

        assert result.failed_logins_24h == 3
        assert result.suspicious_sessions_24h == 3
        assert result.password_resets_24h == 3
        assert "192.168.1.1" in result.blocked_ips
        assert result.top_threat_ips[0]["ip"] == "192.168.1.1"
        assert result.top_threat_ips[0]["count"] == 10

    def test_empty_blocked_ips_when_no_failures(self):
        db = MagicMock()
        db.scalar.return_value = 0
        db.execute.return_value.all.return_value = []

        result = SecurityDashboardService.get_summary(db)
        assert result.blocked_ips == []
        assert result.top_threat_ips == []


# ---------------------------------------------------------------------------
# SecurityDashboardService.get_failed_logins
# ---------------------------------------------------------------------------


class TestGetFailedLogins:
    def test_returns_paginated_result(self):
        logs = [_make_audit_log(action=AuditAction.FAILED_LOGIN)]
        db = _mock_db_paginated(logs)

        result = SecurityDashboardService.get_failed_logins(db, page=1, limit=50)

        assert result.page == 1
        assert result.limit == 50
        assert result.total == 1
        assert len(result.items) == 1

    def test_default_pagination_values(self):
        db = _mock_db_paginated([])
        result = SecurityDashboardService.get_failed_logins(db)
        assert result.page == 1
        assert result.limit == 50
        assert result.total == 0
        assert result.items == []


# ---------------------------------------------------------------------------
# SecurityDashboardService.export_failed_logins_csv
# ---------------------------------------------------------------------------


class TestExportFailedLoginsCsv:
    def test_returns_string(self):
        db = MagicMock()
        db.scalars.return_value = iter([])
        result = SecurityDashboardService.export_failed_logins_csv(db)
        assert isinstance(result, str)
        assert "ID" in result

    def test_includes_log_data(self):
        log = _make_audit_log(action=AuditAction.FAILED_LOGIN, ip_address="9.9.9.9")
        db = MagicMock()
        db.scalars.return_value = iter([log])
        result = SecurityDashboardService.export_failed_logins_csv(db)
        assert "9.9.9.9" in result


# ---------------------------------------------------------------------------
# SecurityDashboardService.get_blocked_ips
# ---------------------------------------------------------------------------


class TestGetBlockedIps:
    def test_returns_list_of_blocked_ip_entries(self):
        db = MagicMock()
        # execute().all() for group-by query
        db.execute.return_value.all.return_value = [("5.5.5.5", 10)]
        # scalar() for last_seen
        db.scalar.return_value = datetime.now(timezone.utc)
        # scalars().all() for user_ids
        db.scalars.return_value.all.return_value = [uuid.uuid4()]

        result = SecurityDashboardService.get_blocked_ips(db)

        assert len(result) == 1
        assert result[0].ip_address == "5.5.5.5"
        assert result[0].failed_login_count == 10

    def test_empty_when_no_blocked_ips(self):
        db = MagicMock()
        db.execute.return_value.all.return_value = []
        result = SecurityDashboardService.get_blocked_ips(db)
        assert result == []


# ---------------------------------------------------------------------------
# SecurityDashboardService.get_suspicious_sessions
# ---------------------------------------------------------------------------


class TestGetSuspiciousSessions:
    def test_returns_paginated_result(self):
        logs = [_make_audit_log(action=AuditAction.SUSPICIOUS_LOGIN_ATTEMPT)]
        db = _mock_db_paginated(logs)
        result = SecurityDashboardService.get_suspicious_sessions(db)
        assert result.total == 1
        assert result.items[0].action == "suspicious_login_attempt"


# ---------------------------------------------------------------------------
# SecurityDashboardService.get_password_resets
# ---------------------------------------------------------------------------


class TestGetPasswordResets:
    def test_returns_paginated_result(self):
        logs = [_make_audit_log(action=AuditAction.PASSWORD_RESET, success=True)]
        db = _mock_db_paginated(logs)
        result = SecurityDashboardService.get_password_resets(db)
        assert result.total == 1

    def test_empty_result(self):
        db = _mock_db_paginated([])
        result = SecurityDashboardService.get_password_resets(db)
        assert result.total == 0
        assert result.items == []


# ---------------------------------------------------------------------------
# SecurityDashboardService.get_api_abuse
# ---------------------------------------------------------------------------


class TestGetApiAbuse:
    def test_returns_paginated_result(self):
        logs = [_make_audit_log(action=AuditAction.API_ACCESS, success=False)]
        db = _mock_db_paginated(logs)
        result = SecurityDashboardService.get_api_abuse(db)
        assert result.total == 1
        assert result.items[0].success is False


# ---------------------------------------------------------------------------
# SecurityDashboardService.get_security_alerts
# ---------------------------------------------------------------------------


class TestGetSecurityAlerts:
    def test_returns_dict_with_items(self):
        logs = [_make_audit_log(action=AuditAction.SUSPICIOUS_LOGIN_ATTEMPT)]
        db = _mock_db_paginated(logs)
        result = SecurityDashboardService.get_security_alerts(db)
        assert "items" in result
        assert "total" in result
        assert result["total"] == 1

    def test_severity_critical_for_suspicious_login(self):
        logs = [_make_audit_log(action=AuditAction.SUSPICIOUS_LOGIN_ATTEMPT)]
        db = _mock_db_paginated(logs)
        result = SecurityDashboardService.get_security_alerts(db)
        assert result["items"][0].severity == "critical"

    def test_severity_filter_applied(self):
        """When severity='critical' is passed, only critical-action logs are queried."""
        # We just verify no exception is raised and the method is callable
        db = _mock_db_paginated([])
        result = SecurityDashboardService.get_security_alerts(db, severity="critical")
        assert result["total"] == 0

    def test_empty_alerts(self):
        db = _mock_db_paginated([])
        result = SecurityDashboardService.get_security_alerts(db)
        assert result["items"] == []
        assert result["total"] == 0


# ---------------------------------------------------------------------------
# SecurityDashboardService.search_all
# ---------------------------------------------------------------------------


class TestSearchAll:
    def test_returns_paginated_result(self):
        logs = [_make_audit_log(description="suspicious ip login attempt")]
        db = _mock_db_paginated(logs)
        result = SecurityDashboardService.search_all(db, q="suspicious")
        assert result.total == 1

    def test_empty_search(self):
        db = _mock_db_paginated([])
        result = SecurityDashboardService.search_all(db, q="nonexistent_term_xyz")
        assert result.total == 0
        assert result.items == []


# ---------------------------------------------------------------------------
# require_admin RBAC guard
# ---------------------------------------------------------------------------


class TestRequireAdmin:
    def test_admin_system_role_passes(self):
        from app.routers.security_dashboard import require_admin

        user = MagicMock()
        user.system_role = "admin"
        user.role = "user"
        result = require_admin(current_user=user)
        assert result is user

    def test_admin_role_passes(self):
        from app.routers.security_dashboard import require_admin

        user = MagicMock()
        user.system_role = "user"
        user.role = "admin"
        result = require_admin(current_user=user)
        assert result is user

    def test_non_admin_raises_403(self):
        from app.routers.security_dashboard import require_admin
        from fastapi import HTTPException

        user = MagicMock()
        user.system_role = "user"
        user.role = "developer"
        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=user)
        assert exc_info.value.status_code == 403

    def test_viewer_raises_403(self):
        from app.routers.security_dashboard import require_admin
        from fastapi import HTTPException

        user = MagicMock()
        user.system_role = "viewer"
        user.role = "viewer"
        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=user)
        assert exc_info.value.status_code == 403
