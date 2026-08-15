from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.request_log import RequestLog
from app.schemas.request_analytics import (
    DailyRequestMetric,
    RequestAnalyticsResponse,
    RequestEndpointMetric,
)


class RequestAnalyticsService:
    """
    Computes API request analytics from the ``request_logs`` table:
    total volume, latency, error rates, active users, rate-limited requests,
    per-endpoint breakdowns, and daily trends.
    """

    @staticmethod
    def get_request_analytics(db: Session, days: int = 30) -> RequestAnalyticsResponse:
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        total_requests = (
            db.scalar(
                select(func.count(RequestLog.id)).where(
                    RequestLog.created_at >= start_date
                )
            )
            or 0
        )

        avg_duration = (
            db.scalar(
                select(func.avg(RequestLog.duration_ms)).where(
                    RequestLog.created_at >= start_date
                )
            )
            or 0.0
        )

        errors = (
            db.scalar(
                select(func.count(RequestLog.id)).where(
                    RequestLog.created_at >= start_date,
                    RequestLog.status_code >= 400,
                )
            )
            or 0
        )

        active_users = (
            db.scalar(
                select(func.count(func.distinct(RequestLog.user_id))).where(
                    RequestLog.created_at >= start_date,
                    RequestLog.user_id.isnot(None),
                )
            )
            or 0
        )

        rate_limited = (
            db.scalar(
                select(func.count(RequestLog.id)).where(
                    RequestLog.created_at >= start_date,
                    RequestLog.is_rate_limited.is_(True),
                )
            )
            or 0
        )

        error_rate_pct = (
            round((errors / total_requests) * 100, 2) if total_requests else 0.0
        )

        # ------------------------------------------------------------------
        # Per-endpoint breakdown
        # ------------------------------------------------------------------
        endpoint_query = (
            select(
                RequestLog.method,
                RequestLog.path,
                func.count(RequestLog.id),
                func.avg(RequestLog.duration_ms),
            )
            .where(RequestLog.created_at >= start_date)
            .group_by(RequestLog.method, RequestLog.path)
        )
        endpoint_durations: Dict[str, float] = {}
        endpoint_counts: Dict[str, int] = {}
        for method, path, count, avg_ms in db.execute(endpoint_query).all():
            key = f"{method} {path}"
            endpoint_counts[key] = count
            endpoint_durations[key] = float(avg_ms or 0.0)

        error_rows = db.execute(
            select(RequestLog.method, RequestLog.path, func.count(RequestLog.id))
            .where(
                RequestLog.created_at >= start_date,
                RequestLog.status_code >= 400,
            )
            .group_by(RequestLog.method, RequestLog.path)
        ).all()
        endpoint_errors: Dict[str, int] = {}
        for method, path, count in error_rows:
            endpoint_errors[f"{method} {path}"] = count

        requests_by_endpoint: List[RequestEndpointMetric] = []
        for key, count in endpoint_counts.items():
            method, path = key.split(" ", 1)
            error_count = endpoint_errors.get(key, 0)
            avg_ms = endpoint_durations.get(key, 0.0)
            requests_by_endpoint.append(
                RequestEndpointMetric(
                    endpoint=path,
                    method=method,
                    requests=count,
                    avg_response_time_ms=round(float(avg_ms), 2),
                    error_count=error_count,
                    error_rate_pct=round((error_count / count) * 100, 2),
                )
            )
        requests_by_endpoint.sort(key=lambda m: m.requests, reverse=True)

        # ------------------------------------------------------------------
        # Daily trend
        # ------------------------------------------------------------------
        daily_rows = db.execute(
            select(
                func.date(RequestLog.created_at).label("date"),
                func.count(RequestLog.id).label("requests"),
            )
            .where(RequestLog.created_at >= start_date)
            .group_by(func.date(RequestLog.created_at))
            .order_by(func.date(RequestLog.created_at))
        ).all()

        daily_error_rows = db.execute(
            select(
                func.date(RequestLog.created_at).label("date"),
                func.count(RequestLog.id).label("errors"),
            )
            .where(
                RequestLog.created_at >= start_date,
                RequestLog.status_code >= 400,
            )
            .group_by(func.date(RequestLog.created_at))
        ).all()
        daily_error_counts = {str(date): errors for date, errors in daily_error_rows}

        daily_trend = [
            DailyRequestMetric(
                date=str(date),
                requests=int(requests),
                errors=int(daily_error_counts.get(str(date), 0)),
            )
            for date, requests in daily_rows
        ]

        return RequestAnalyticsResponse(
            timeframe_days=days,
            total_requests=total_requests,
            avg_response_time_ms=round(float(avg_duration), 2),
            error_rate_pct=error_rate_pct,
            active_users=active_users,
            rate_limited_requests=rate_limited,
            requests_by_endpoint=requests_by_endpoint,
            daily_trend=daily_trend,
        )

    @staticmethod
    def export_csv(db: Session, days: int = 30) -> str:
        """Returns a CSV string of request logs for the given window."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        rows = (
            db.execute(
                select(RequestLog)
                .where(RequestLog.created_at >= start_date)
                .order_by(RequestLog.created_at.desc())
                .limit(10000)
            )
            .scalars()
            .all()
        )

        lines = ["timestamp,method,path,status_code,duration_ms,user_id,rate_limited"]
        for log in rows:
            lines.append(
                ",".join(
                    [
                        log.created_at.isoformat(),
                        log.method,
                        log.path,
                        str(log.status_code),
                        str(log.duration_ms),
                        log.user_id or "",
                        "1" if log.is_rate_limited else "0",
                    ]
                )
            )
        return "\n".join(lines)
