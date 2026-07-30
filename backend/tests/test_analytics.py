from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.application import Application, ApplicationStatus
from app.models.builder_flare import BuilderFlare
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.user import User
from app.services.analytics_service import AnalyticsService

# Create in-memory SQLite engine for testing
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


def test_empty_platform_analytics():
    db = TestingSessionLocal()
    result = AnalyticsService.get_platform_analytics(db=db, days=30)
    db.close()

    assert result.timeframe_days == 30
    assert result.active_users.dau == 0
    assert result.active_users.wau == 0
    assert result.active_users.mau == 0
    assert result.retention.retention_7d_pct == 0.0
    assert result.conversion.profile_completion_pct == 0.0
    assert result.project_growth.total_projects == 0


def test_analytics_with_data():
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)

    # 1. Create Users
    u1 = User(
        first_name="Active",
        last_name="User",
        username="active_user",
        email="active@example.com",
        password_hash="hashed",
        is_active=True,
        last_login=now,
        headline="Software Engineer",
        created_at=now - timedelta(days=10),
    )
    u2 = User(
        first_name="Inactive",
        last_name="User",
        username="inactive_user",
        email="inactive@example.com",
        password_hash="hashed",
        is_active=True,
        last_login=now - timedelta(days=40),
        created_at=now - timedelta(days=50),
    )
    db.add_all([u1, u2])
    db.commit()
    db.refresh(u1)
    db.refresh(u2)

    # 2. Create Project
    p1 = Project(
        owner_id=u1.id,
        title="DevLink Project",
        slug="devlink-project",
        description="Collaborative platform",
        stage=ProjectStage.MVP,
        visibility=ProjectVisibility.PUBLIC,
        created_at=now - timedelta(days=5),
    )
    db.add(p1)
    db.commit()
    db.refresh(p1)

    # 3. Create Builder Flare & Application
    flare = BuilderFlare(
        project_id=p1.id,
        created_by=u1.id,
        title="Backend Dev",
        description="Python FastAPI developer needed",
        role="Backend Dev",
    )
    db.add(flare)
    db.commit()
    db.refresh(flare)

    app1 = Application(
        applicant_id=u1.id,
        project_id=p1.id,
        flare_id=flare.id,
        status=ApplicationStatus.ACCEPTED,
        message="Interested in backend work",
    )
    db.add(app1)
    db.commit()

    # Query analytics service
    result = AnalyticsService.get_platform_analytics(db=db, days=30)
    db.close()

    assert result.active_users.dau == 1
    assert result.active_users.wau == 1
    assert result.active_users.mau == 1
    assert result.project_growth.total_projects == 1
    assert result.project_growth.new_projects_period == 1
    assert result.conversion.completed_profiles_count == 1
    assert result.conversion.project_creators_count == 1
    assert result.conversion.accepted_applications_count == 1
    assert result.conversion.application_acceptance_pct == 100.0


def test_analytics_api_endpoint():
    response = client.get("/api/analytics?days=14")
    assert response.status_code == 200
    data = response.json()

    assert data["timeframe_days"] == 14
    assert "active_users" in data
    assert "retention" in data
    assert "conversion" in data
    assert "project_growth" in data
    assert "dau" in data["active_users"]
    assert "wau" in data["active_users"]
    assert "mau" in data["active_users"]


def test_analytics_overview_endpoint():
    response = client.get("/api/analytics/overview")
    assert response.status_code == 200
    data = response.json()

    assert "dau" in data
    assert "wau" in data
    assert "mau" in data
    assert "retention_7d_pct" in data
    assert "conversion" not in data or isinstance(
        data.get("profile_completion_pct"), (int, float)
    )
