import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class AnalyticsEventCreate(BaseModel):
    event_type: str = Field(
        ...,
        description="Type of event: user_registration, project_creation, application_sent, profile_view, search_performed, message_sent, team_invitation_sent",
    )
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Custom event metadata properties"
    )
    session_id: Optional[str] = None


class AnalyticsEventResponse(BaseModel):
    id: str
    event_type: str
    user_id: Optional[uuid.UUID] = None
    properties: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EventTypeMetric(BaseModel):
    event_type: str
    count: int


class AnalyticsMetricsSummary(BaseModel):
    total_events: int
    event_counts: Dict[str, int]
    period_days: int
