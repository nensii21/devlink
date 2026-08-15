import json
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session

from app.models.search_analytics import SearchQueryLog, SearchClickLog


class SearchAnalyticsService:
    @staticmethod
    def log_search(
        db: Session,
        query: str,
        results_count: int,
        latency_ms: float,
        user_id: Optional[uuid.UUID] = None,
        filters: Optional[Dict] = None,
    ) -> uuid.UUID:

        log_entry = SearchQueryLog(
            query=query,
            user_id=user_id,
            results_count=results_count,
            latency_ms=latency_ms,
            filters=json.dumps(filters) if filters else None,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry.id

    @staticmethod
    def log_click(
        db: Session,
        search_query_id: uuid.UUID,
        clicked_entity_type: str,
        clicked_entity_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> None:

        click_entry = SearchClickLog(
            search_query_id=search_query_id,
            clicked_entity_type=clicked_entity_type,
            clicked_entity_id=clicked_entity_id,
            user_id=user_id,
        )
        db.add(click_entry)
        db.commit()

    @staticmethod
    def get_dashboard_metrics(db: Session, days: int = 30) -> Dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # 1. Total Searches
        total_searches = (
            db.scalar(
                select(func.count())
                .select_from(SearchQueryLog)
                .where(SearchQueryLog.created_at >= cutoff)
            )
            or 0
        )

        # 2. Average Latency
        avg_latency = (
            db.scalar(
                select(func.avg(SearchQueryLog.latency_ms)).where(
                    SearchQueryLog.created_at >= cutoff
                )
            )
            or 0.0
        )

        # 3. Zero-result Searches
        zero_results_count = (
            db.scalar(
                select(func.count())
                .select_from(SearchQueryLog)
                .where(
                    SearchQueryLog.created_at >= cutoff,
                    SearchQueryLog.results_count == 0,
                )
            )
            or 0
        )

        zero_result_rate = (
            (zero_results_count / total_searches * 100) if total_searches > 0 else 0.0
        )

        # 4. Click-Through Rate (CTR)
        # CTR = Queries with at least one click / Total Queries
        queries_with_clicks = (
            db.scalar(
                select(func.count(func.distinct(SearchClickLog.search_query_id))).where(
                    SearchClickLog.created_at >= cutoff
                )
            )
            or 0
        )
        ctr = (
            (queries_with_clicks / total_searches * 100) if total_searches > 0 else 0.0
        )

        # 5. Top 10 Searched Keywords
        top_keywords = db.execute(
            select(SearchQueryLog.query, func.count(SearchQueryLog.id).label("count"))
            .where(SearchQueryLog.created_at >= cutoff)
            .group_by(SearchQueryLog.query)
            .order_by(desc("count"))
            .limit(10)
        ).all()

        return {
            "total_searches": total_searches,
            "average_latency_ms": round(avg_latency, 2),
            "zero_result_rate_pct": round(zero_result_rate, 2),
            "click_through_rate_pct": round(ctr, 2),
            "top_keywords": [
                {"keyword": row[0], "count": row[1]} for row in top_keywords
            ],
        }
