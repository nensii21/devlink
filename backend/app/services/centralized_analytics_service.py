import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.centralized_analytics import (
    CentralizedAnalyticsEvent,
)
from app.schemas.centralized_analytics import AnalyticsMetricsSummary


class CentralizedAnalyticsService:
    @staticmethod
    def track_event(
        db: Session,
        event_type: str,
        user_id: Optional[uuid.UUID] = None,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CentralizedAnalyticsEvent:
        event = CentralizedAnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            properties=properties or {},
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_metrics(
        db: Session,
        days: int = 30,
    ) -> AnalyticsMetricsSummary:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        query = (
            db.query(
                CentralizedAnalyticsEvent.event_type,
                func.count(CentralizedAnalyticsEvent.id).label("cnt"),
            )
            .filter(CentralizedAnalyticsEvent.created_at >= cutoff)
            .group_by(CentralizedAnalyticsEvent.event_type)
        )

        event_counts: Dict[str, int] = {}
        total = 0
        for event_type, cnt in query.all():
            event_counts[event_type] = cnt
            total += cnt

        return AnalyticsMetricsSummary(
            total_events=total,
            event_counts=event_counts,
            period_days=days,
        )

    @staticmethod
    def list_events(
        db: Session,
        limit: int = 50,
        event_type: Optional[str] = None,
    ) -> List[CentralizedAnalyticsEvent]:
        query = db.query(CentralizedAnalyticsEvent)
        if event_type:
            query = query.filter(CentralizedAnalyticsEvent.event_type == event_type)
        return (
            query.order_by(CentralizedAnalyticsEvent.created_at.desc())
            .limit(limit)
            .all()
        )
