"""
Pydantic schemas for the Security Audit Dashboard (Issue #622).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Shared audit log response
# ---------------------------------------------------------------------------


class SecurityAuditLogItem(BaseModel):
    """Single audit log entry returned by dashboard endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    target_user_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    success: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    metadata_info: Optional[dict[str, Any]] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Paginated response wrapper
# ---------------------------------------------------------------------------


class PaginatedSecurityLogs(BaseModel):
    """Paginated wrapper returned by all dashboard list endpoints."""

    items: list[SecurityAuditLogItem]
    total: int
    page: int
    limit: int
    pages: int


# ---------------------------------------------------------------------------
# Dashboard summary (overview section)
# ---------------------------------------------------------------------------


class SecurityDashboardSummary(BaseModel):
    """Aggregated counters for the dashboard overview."""

    failed_logins_24h: int
    failed_logins_7d: int
    suspicious_sessions_24h: int
    password_resets_24h: int
    api_abuse_events_24h: int
    total_security_alerts_24h: int
    blocked_ips: list[str]  # IPs that generated ≥ threshold failures
    top_threat_ips: list[dict[str, Any]]  # [{ip, count}]


# ---------------------------------------------------------------------------
# IP block entry
# ---------------------------------------------------------------------------


class BlockedIPEntry(BaseModel):
    """An IP address flagged as suspicious with event statistics."""

    ip_address: str
    failed_login_count: int
    last_seen: Optional[datetime] = None
    associated_user_ids: list[str] = []


# ---------------------------------------------------------------------------
# Security alert
# ---------------------------------------------------------------------------


class SecurityAlertItem(BaseModel):
    """A high-priority security alert."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action: str
    description: Optional[str] = None
    ip_address: Optional[str] = None
    actor_id: Optional[uuid.UUID] = None
    created_at: datetime
    severity: str  # "critical" | "high" | "medium"
