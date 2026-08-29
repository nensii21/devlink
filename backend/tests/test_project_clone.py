import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.project import ProjectStage, ProjectVisibility
from app.models.user import User
from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService
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


def _create_user(db, email: str, username: str) -> User:
    user = User(
        email=email,
        username=username,
        first_name=username.capitalize(),
        last_name="Test",
        password_hash="fakehash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_clone_project_success():
    client = TestClient(app)
    db = TestingSessionLocal()

    user = _create_user(db, "clone_user@example.com", "cloneuser")
    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    original_project_in = ProjectCreate(
        title="Original Test Project",
        slug="original-test-project",
        tagline="Original Tagline",
        description="Original Description",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
    )
    original_project = ProjectService.create_project(db, user.id, original_project_in)

    response = client.post(
        f"/api/projects/{original_project.id}/clone",
        headers=headers,
        json={
            "title": "Cloned Test Project",
            "tagline": "Custom Cloned Tagline",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Cloned Test Project"
    assert data["tagline"] == "Custom Cloned Tagline"
    assert data["owner_id"] == str(user.id)
    assert data["id"] != str(original_project.id)
    assert data["stars"] == 0
    assert data["views"] == 0


def test_clone_project_default_title_fallback():
    client = TestClient(app)
    db = TestingSessionLocal()

    user = _create_user(db, "clone_user2@example.com", "cloneuser2")
    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    original = ProjectService.create_project(
        db,
        user.id,
        ProjectCreate(
            title="Base Project",
            slug="base-project",
            description="Base Description",
            stage=ProjectStage.MVP,
            visibility=ProjectVisibility.PUBLIC,
        ),
    )

    response = client.post(
        f"/api/projects/{original.id}/clone",
        headers=headers,
        json={},
    )

    assert response.status_code == 201
    data = response.json()
    assert "Base Project (Copy)" in data["title"]
    assert data["slug"] == "base-project-copy"
    assert data["owner_id"] == str(user.id)


def test_clone_project_unauthorized():
    client = TestClient(app)
    db = TestingSessionLocal()

    user = _create_user(db, "owner@example.com", "owner")
    original = ProjectService.create_project(
        db,
        user.id,
        ProjectCreate(
            title="Public Project",
            slug="public-project",
            description="Public Description",
            stage=ProjectStage.IDEA,
            visibility=ProjectVisibility.PUBLIC,
        ),
    )

    response = client.post(f"/api/projects/{original.id}/clone")
    assert response.status_code == 401


def test_clone_project_not_found():
    client = TestClient(app)
    db = TestingSessionLocal()

    user = _create_user(db, "owner2@example.com", "owner2")
    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    random_id = uuid.uuid4()
    response = client.post(
        f"/api/projects/{random_id}/clone",
        headers=headers,
    )
    assert response.status_code == 404
