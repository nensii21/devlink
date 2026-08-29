import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database
from app.database.session import get_db
from app.main import app
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.organization import Organization, OrganizationType
from app.models.hackathon import Hackathon, HackathonStatus

# SQLite setup for tests
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_database] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_social_proof_endpoint():
    client = TestClient(app)
    db = TestingSessionLocal()

    # 1. Check initial empty state
    res = client.get("/api/analytics/social-proof")
    assert res.status_code == 200
    data = res.json()
    assert "developers" in data
    assert "projects" in data
    assert "teams" in data
    assert "organizations" in data
    assert "hackathons" in data
    assert "last_updated" in data
    assert data["developers"] == 0

    # 2. Add sample data
    user1 = User(
        email="dev1@example.com",
        username="dev1",
        first_name="Dev",
        last_name="One",
        password_hash="fakehash",
        is_active=True,
    )
    user2 = User(
        email="dev2@example.com",
        username="dev2",
        first_name="Dev",
        last_name="Two",
        password_hash="fakehash",
        is_active=True,
    )
    db.add_all([user1, user2])
    db.commit()
    db.refresh(user1)
    db.refresh(user2)

    proj = Project(
        owner_id=user1.id,
        title="Social Proof Proj",
        slug="social-proof-proj",
        description="Demo project",
        is_published=True,
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)

    member = ProjectMember(
        project_id=proj.id,
        user_id=user2.id,
        role="developer",
        is_active=True,
    )
    db.add(member)

    org = Organization(
        owner_id=user1.id,
        name="DevLink Labs",
        slug="devlink-labs",
        organization_type=OrganizationType.STARTUP,
    )
    db.add(org)

    now = datetime.now(timezone.utc)
    hackathon = Hackathon(
        created_by=user1.id,
        name="DevLink AI Hackathon",
        description="Build AI tools",
        status=HackathonStatus.REGISTRATION_OPEN,
        starts_at=now,
        ends_at=now,
    )
    db.add(hackathon)
    db.commit()

    # 3. Query social proof again and verify counts
    res2 = client.get("/api/analytics/social-proof")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["developers"] == 2
    assert data2["projects"] == 1
    assert data2["teams"] == 1
    assert data2["organizations"] == 1
    assert data2["hackathons"] == 1
