from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database, get_current_user
from app.main import app
from app.models.user import User
from app.models.project import Project, ProjectStage, ProjectVisibility
from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService

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


def test_get_project_by_id_increments_views():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, "owner@example.com", "owner")

    project_in = ProjectCreate(
        title="Test Project ID",
        slug="test-project-id",
        description="A project to test views by ID.",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
    )
    project = ProjectService.create_project(db, user.id, project_in)
    project_id = str(project.id)

    # Views should initially be 0
    assert project.views == 0

    # Request the project by ID
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["views"] == 1

    # Request the project again by ID
    response2 = client.get(f"/api/projects/{project_id}")
    assert response2.status_code == 200
    assert response2.json()["views"] == 2

    db.close()


def test_get_project_by_slug_increments_views():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, "owner2@example.com", "owner2")

    project_in = ProjectCreate(
        title="Test Project Slug",
        slug="test-project-slug",
        description="A project to test views by slug.",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
    )
    project = ProjectService.create_project(db, user.id, project_in)
    project_slug = project.slug

    # Views should initially be 0
    assert project.views == 0

    # Request the project by slug
    response = client.get(f"/api/projects/slug/{project_slug}")
    assert response.status_code == 200
    assert response.json()["views"] == 1

    # Request the project again by slug
    response2 = client.get(f"/api/projects/slug/{project_slug}")
    assert response2.status_code == 200
    assert response2.json()["views"] == 2

    db.close()


def test_list_projects_does_not_increment_views():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, "owner3@example.com", "owner3")

    project_in = ProjectCreate(
        title="Test Project List",
        slug="test-project-list",
        description="A project to test views in list.",
        stage=ProjectStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
    )
    project = ProjectService.create_project(db, user.id, project_in)

    # List projects
    response = client.get("/api/projects/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # The view count should remain 0 in the list response
    list_project = next(p for p in data if p["slug"] == "test-project-list")
    assert list_project["views"] == 0

    # Refresh from DB to ensure it wasn't modified
    db.refresh(project)
    assert project.views == 0

    db.close()
