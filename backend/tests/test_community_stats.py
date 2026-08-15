from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.application import Application, ApplicationStatus
from app.models.builder_flare import BuilderFlare, FlareStatus
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.project_member import ProjectMember
from app.models.skill import Skill
from app.models.user import User
from app.models.user_skill import UserSkill
from app.services.community_stats_service import CommunityStatsService

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


def test_empty_community_stats():
    db = TestingSessionLocal()
    result = CommunityStatsService.get_community_stats(db=db, days=30)
    db.close()

    assert result.timeframe_days == 30
    assert result.total_developers == 0
    assert result.active_projects == 0
    assert result.teams_formed == 0
    assert result.open_opportunities == 0
    assert result.contributions_this_month == 0
    assert result.new_users_this_month == 0
    assert result.most_popular_skills == []
    assert result.trending_technologies == []


def test_community_stats_with_data():
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)

    # 1. Active + new developers
    u1 = User(
        first_name="Dev",
        last_name="One",
        username="dev_one",
        email="dev1@example.com",
        password_hash="hashed",
        is_active=True,
        created_at=now,
    )
    u2 = User(
        first_name="Dev",
        last_name="Two",
        username="dev_two",
        email="dev2@example.com",
        password_hash="hashed",
        is_active=True,
        created_at=now - timedelta(days=90),
    )
    # Inactive (soft deleted) user must not count
    u3 = User(
        first_name="Gone",
        last_name="User",
        username="gone_user",
        email="gone@example.com",
        password_hash="hashed",
        is_active=True,
        deleted_at=now,
    )
    db.add_all([u1, u2, u3])
    db.commit()
    db.refresh(u1)
    db.refresh(u2)

    # 2. Skills
    s_python = Skill(name="Python", normalized_name="python", slug="python")
    s_react = Skill(name="React", normalized_name="react", slug="react")
    db.add_all([s_python, s_react])
    db.commit()
    db.refresh(s_python)
    db.refresh(s_react)

    db.add_all(
        [
            UserSkill(user_id=u1.id, skill_id=s_python.id),
            UserSkill(user_id=u2.id, skill_id=s_python.id),
            UserSkill(user_id=u1.id, skill_id=s_react.id),
        ]
    )
    db.commit()

    # 3. Active + archived projects with languages and tags
    p1 = Project(
        owner_id=u1.id,
        title="Active Project",
        slug="active-project",
        description="Active project",
        stage=ProjectStage.MVP,
        visibility=ProjectVisibility.PUBLIC,
        language="Python",
        tags=["FastAPI", "Docker"],
        created_at=now - timedelta(days=5),
    )
    p2 = Project(
        owner_id=u2.id,
        title="Archived Project",
        slug="archived-project",
        description="Archived project",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
        language="Python",
        is_archived=True,
        created_at=now - timedelta(days=10),
    )
    db.add_all([p1, p2])
    db.commit()
    db.refresh(p1)

    # 4. Team formed (active members on p1)
    db.add(ProjectMember(project_id=p1.id, user_id=u2.id))
    db.commit()

    # 5. Open opportunity
    flare = BuilderFlare(
        project_id=p1.id,
        created_by=u1.id,
        title="Backend Dev",
        description="Python developer needed",
        role="Backend Dev",
        status=FlareStatus.OPEN,
    )
    db.add(flare)
    db.commit()
    db.refresh(flare)

    # 6. Accepted application this month = contribution
    app1 = Application(
        applicant_id=u2.id,
        project_id=p1.id,
        flare_id=flare.id,
        status=ApplicationStatus.ACCEPTED,
        updated_at=now,
    )
    db.add(app1)
    db.commit()

    result = CommunityStatsService.get_community_stats(db=db, days=30)
    db.close()

    assert result.total_developers == 2
    assert result.active_projects == 1
    assert result.teams_formed == 1
    assert result.open_opportunities == 1
    assert result.contributions_this_month == 1
    assert result.new_users_this_month == 1

    skill_map = {s.name: s.count for s in result.most_popular_skills}
    assert skill_map.get("Python") == 2
    assert skill_map.get("React") == 1

    tech_map = {t.name: t.count for t in result.trending_technologies}
    assert tech_map.get("Python") == 1
    assert tech_map.get("FastAPI") == 1
    assert tech_map.get("Docker") == 1
    assert (
        "Python" not in {t.name for t in result.trending_technologies}
        or tech_map.get("Python") >= 1
    )


def test_community_stats_requires_admin():
    response = client.get("/api/analytics/community/stats")
    assert response.status_code == 401
