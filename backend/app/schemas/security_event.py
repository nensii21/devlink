from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.security_event import SecurityEventSeverity, SecurityEventType


class SecurityEventCreate(BaseModel):
    event_type: SecurityEventType = Field(
        description="Security event classification type"
    )
    description: str = Field(
        ..., min_length=1, description="Event description or error message"
    )
    severity: Optional[SecurityEventSeverity] = Field(
        default=None,
        description="Optional explicit severity level (info, low, medium, high, critical)",
    )
    risk_score: Optional[float] = Field(
        default=0.0, ge=0.0, le=1.0, description="Computed risk score (0.0 to 1.0)"
    )
    actor_id: Optional[uuid.UUID] = Field(
        default=None, description="User ID of actor initiating action"
    )
    target_user_id: Optional[uuid.UUID] = Field(
        default=None, description="Target user ID affected"
    )
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client User-Agent")
    request_method: Optional[str] = Field(
        default=None, description="HTTP method (POST, GET, etc.)"
    )
    request_path: Optional[str] = Field(
        default=None, description="HTTP request URI path"
    )
    metadata_payload: Optional[dict[str, Any]] = Field(
        default=None, description="Additional context payload"
    )


class SecurityEventResolveRequest(BaseModel):
    resolution_notes: Optional[str] = Field(
        default=None, description="Administrative notes regarding event resolution"
    )


class SecurityEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    severity: str
    risk_score: float
    description: str
    actor_id: Optional[uuid.UUID] = None
    target_user_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    alert_triggered: bool = False
    alert_message: Optional[str] = None
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None
    metadata_payload: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedSecurityEventsResponse(BaseModel):
    items: list[SecurityEventResponse]
    total: int
    page: int
    limit: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class TopOffendingIPItem(BaseModel):
    ip_address: str
    event_count: int
    critical_alerts_count: int


class SecurityEventSummaryResponse(BaseModel):
    total_events: int
    events_24h: int
    alerts_triggered_total: int
    unresolved_alerts_count: int
    critical_alerts_24h: int
    event_type_breakdown: dict[str, int]
    severity_breakdown: dict[str, int]
    top_offending_ips: list[TopOffendingIPItem]
