import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.user import User
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.core.security import create_access_token

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
    app.dependency_overrides[get_database] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_get_user_by_username():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = User(
        email="realuser@example.com",
        username="realuser",
        first_name="Real",
        last_name="Developer",
        bio="Building open-source software.",
        location="Berlin, Germany",
        website="https://realdev.io",
        role="Backend Architect",
        password_hash="fakehash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.get("/api/users/by-username/realuser")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "realuser"
    assert data["first_name"] == "Real"
    assert data["last_name"] == "Developer"
    assert data["bio"] == "Building open-source software."
    assert data["location"] == "Berlin, Germany"
    assert data["role"] == "Backend Architect"


def test_get_user_by_username_not_found():
    client = TestClient(app)
    response = client.get("/api/users/by-username/nonexistent_user")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_list_user_projects():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = User(
        email="creator@example.com",
        username="creator",
        first_name="Project",
        last_name="Creator",
        password_hash="fakehash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    proj1 = Project(
        title="DevLink Platform",
        slug="devlink-platform",
        description="A great developer platform",
        stage=ProjectStage.MVP,
        visibility=ProjectVisibility.PUBLIC,
        owner_id=user.id,
    )
    proj2 = Project(
        title="AI Assistant",
        slug="ai-assistant",
        description="An AI assistant app",
        stage=ProjectStage.BETA,
        visibility=ProjectVisibility.PUBLIC,
        owner_id=user.id,
    )
    db.add_all([proj1, proj2])
    db.commit()

    response = client.get(f"/api/projects/user/{user.id}")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 2
    slugs = [p["slug"] for p in projects]
    assert "devlink-platform" in slugs
    assert "ai-assistant" in slugs
