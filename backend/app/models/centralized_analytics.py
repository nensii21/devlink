import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class AnalyticsEventType(str, Enum):
    USER_REGISTRATION = "user_registration"
    PROJECT_CREATION = "project_creation"
    APPLICATION_SENT = "application_sent"
    PROFILE_VIEW = "profile_view"
    SEARCH_PERFORMED = "search_performed"
    MESSAGE_SENT = "message_sent"
    TEAM_INVITATION_SENT = "team_invitation_sent"


class CentralizedAnalyticsEvent(Base):
    __tablename__ = "centralized_analytics_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    properties = Column(JSON, nullable=True, default=dict)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    user = relationship("User", foreign_keys=[user_id])
