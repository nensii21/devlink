from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.user import User
from app.models.profile_view import ProfileView
from app.models.follower import Follower
from app.services.analytics_service import AnalyticsService

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_empty_profile_analytics():
    db = TestingSessionLocal()
    user_id = uuid.uuid4()
    result = AnalyticsService.get_profile_analytics(db=db, user_id=user_id)
    db.close()

    assert result.summary.profile_views.total == 0
    assert result.summary.profile_views.growth_pct == 0.0
    assert result.summary.search_appearances.total == 0
    assert len(result.trends) == 7


def test_profile_analytics_with_data():
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)

    # Create target user
    user = User(
        first_name="Target",
        last_name="User",
        username="target_user",
        email="target@example.com",
        password_hash="hashed",
        is_active=True,
    )
    # Create viewer user
    viewer = User(
        first_name="Viewer",
        last_name="User",
        username="viewer_user",
        email="viewer@example.com",
        password_hash="hashed",
        is_active=True,
    )
    db.add_all([user, viewer])
    db.commit()
    db.refresh(user)
    db.refresh(viewer)

    # 1. Profile Views
    v1 = ProfileView(viewed_user_id=user.id, viewer_id=viewer.id, created_at=now)
    v2 = ProfileView(
        viewed_user_id=user.id, viewer_id=viewer.id, created_at=now - timedelta(days=8)
    )
    db.add_all([v1, v2])

    # 2. Follower (Connection Request)
    f1 = Follower(follower_id=viewer.id, following_id=user.id, created_at=now)
    db.add(f1)

    # 3. Clicks (logged via service)
    AnalyticsService.log_profile_click(
        db=db, click_type="repository", target_user_id=user.id, user_id=viewer.id
    )
    AnalyticsService.log_profile_click(
        db=db, click_type="project", target_user_id=user.id, user_id=viewer.id
    )

    db.commit()

    # Query
    result = AnalyticsService.get_profile_analytics(db=db, user_id=user.id)
    db.close()

    assert result.summary.profile_views.total == 2
    assert result.summary.profile_views.growth_pct == 0.0

    assert result.summary.connection_requests.total == 1
    assert result.summary.repository_clicks.total == 1
    assert result.summary.project_clicks.total == 1


def test_profile_analytics_endpoints():
    db = TestingSessionLocal()
    # Create user for auth
    user = User(
        first_name="Test",
        last_name="User",
        username="test_user",
        email="test@example.com",
        password_hash="hashed",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    # Authenticate dependencies override
    from app.dependencies import get_current_user, get_optional_current_user

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_optional_current_user] = lambda: user

    # 1. Test GET /profile
    response = client.get("/api/analytics/profile")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "trends" in data
    assert data["summary"]["profile_views"]["total"] == 0

    # 2. Test POST /profile/click
    click_payload = {
        "click_type": "repository",
        "target_user_id": str(user.id),
    }
    response = client.post("/api/analytics/profile/click", json=click_payload)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    # Clean up overrides
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_optional_current_user, None)


def test_profile_analytics_trends_have_expected_days():
    db = TestingSessionLocal()
    user_id = uuid.uuid4()

    result = AnalyticsService.get_profile_analytics(db=db, user_id=user_id)
    db.close()

    assert len(result.trends) == 7
    assert all(trend.date is not None for trend in result.trends)
