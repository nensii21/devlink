from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.request_log import RequestLog
from app.services.request_analytics_service import RequestAnalyticsService

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed(db):
    now = datetime.now(timezone.utc)
    db.add_all(
        [
            RequestLog(
                method="GET",
                path="/api/projects",
                status_code=200,
                duration_ms=12.5,
                user_id="u1",
            ),
            RequestLog(
                method="GET",
                path="/api/projects",
                status_code=200,
                duration_ms=8.2,
                user_id="u1",
            ),
            RequestLog(
                method="GET",
                path="/api/users/me",
                status_code=500,
                duration_ms=40.0,
                user_id="u2",
            ),
            RequestLog(
                method="GET",
                path="/api/search",
                status_code=429,
                duration_ms=3.1,
                user_id=None,
                is_rate_limited=True,
            ),
            RequestLog(
                method="POST",
                path="/api/auth/login",
                status_code=200,
                duration_ms=25.0,
                user_id="u2",
                created_at=now - timedelta(days=31),
            ),
        ]
    )
    db.commit()


def test_request_analytics_metrics():
    Base.metadata.create_all(bind=engine)
    try:
        db = TestingSessionLocal()
        _seed(db)
        result = RequestAnalyticsService.get_request_analytics(db=db, days=30)
        db.close()

        assert result.total_requests == 4
        assert result.avg_response_time_ms > 0
        assert result.active_users == 2
        assert result.rate_limited_requests == 1
        assert result.error_rate_pct > 0

        by_endpoint = {m.endpoint: m for m in result.requests_by_endpoint}
        assert "/api/projects" in by_endpoint
        assert by_endpoint["/api/projects"].requests == 2
        assert by_endpoint["/api/users/me"].error_count == 1

        assert len(result.daily_trend) >= 1
    finally:
        Base.metadata.drop_all(bind=engine)


def test_request_analytics_csv():
    Base.metadata.create_all(bind=engine)
    try:
        db = TestingSessionLocal()
        _seed(db)
        csv_data = RequestAnalyticsService.export_csv(db=db, days=30)
        db.close()

        lines = csv_data.strip().split("\n")
        assert (
            lines[0]
            == "timestamp,method,path,status_code,duration_ms,user_id,rate_limited"
        )
        assert len(lines) == 5
        assert ",/api/search,429," in csv_data
        assert ",1\n" in csv_data
    finally:
        Base.metadata.drop_all(bind=engine)
