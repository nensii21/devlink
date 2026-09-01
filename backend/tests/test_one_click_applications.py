import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_current_user, get_database
from app.main import app
from app.models.application import Application, ApplicationStatus
from app.models.project import Project
from app.models.user import User

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def _create_user(db, email: str, username: str) -> User:
    user = User(
        email=email,
        username=username,
        first_name="Jane",
        last_name="Developer",
        password_hash="fakehash",
        headline="Senior Frontend Engineer",
        github_url="https://github.com/janedev",
        portfolio_url="https://jane.dev",
        resume_url="https://jane.dev/resume.pdf",
        role="Frontend Developer",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_project(db, owner: User, title: str = "DevLink App") -> Project:
    slug = title.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    project = Project(
        title=title,
        slug=slug,
        description="A cool open-source project",
        owner_id=owner.id,
        applications_count=0,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_get_application_prefill(db_session):
    applicant = _create_user(db_session, email="prefill@devlink.io", username="prefilluser")

    def override_get_database():
        return db_session

    def override_get_current_user():
        return applicant

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)
        headers = {"Origin": "http://localhost:3000"}
        response = client.get("/api/applications/prefill", headers=headers)
        assert response.status_code == 200, response.text

        data = response.json()
        assert data["full_name"] == "Jane Developer"
        assert data["username"] == "prefilluser"
        assert data["headline"] == "Senior Frontend Engineer"
        assert data["github_url"] == "https://github.com/janedev"
        assert data["portfolio_url"] == "https://jane.dev"
        assert data["resume_url"] == "https://jane.dev/resume.pdf"
        assert "Senior Frontend Engineer" in data["suggested_cover_letter"]
    finally:
        app.dependency_overrides.clear()


def test_one_click_apply_success(db_session):
    owner = _create_user(db_session, email="owner@devlink.io", username="projowner")
    applicant = _create_user(db_session, email="applicant@devlink.io", username="applicantuser")
    project = _create_project(db_session, owner=owner, title="Open Source Platform")

    def override_get_database():
        return db_session

    def override_get_current_user():
        return applicant

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)
        headers = {"Origin": "http://localhost:3000"}

        payload = {
            "project_id": str(project.id),
            "selected_role": "Frontend Developer",
            "cover_letter": "I'd love to build UI components for this platform!",
            "auto_use_profile": True,
        }

        response = client.post("/api/applications/one-click", json=payload, headers=headers)
        assert response.status_code == 201, response.text

        data = response.json()
        assert data["project_id"] == str(project.id)
        assert data["status"] == "pending"
        assert data["github_url"] == "https://github.com/janedev"
        assert data["portfolio_url"] == "https://jane.dev"
        assert data["resume_url"] == "https://jane.dev/resume.pdf"
    finally:
        app.dependency_overrides.clear()


def test_one_click_apply_duplicate_conflict(db_session):
    owner = _create_user(db_session, email="owner2@devlink.io", username="projowner2")
    applicant = _create_user(db_session, email="applicant2@devlink.io", username="applicantuser2")
    project = _create_project(db_session, owner=owner, title="Duplicate Project Test")

    def override_get_database():
        return db_session

    def override_get_current_user():
        return applicant

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)
        headers = {"Origin": "http://localhost:3000"}

        payload = {
            "project_id": str(project.id),
            "cover_letter": "First application submission",
        }

        res1 = client.post("/api/applications/one-click", json=payload, headers=headers)
        assert res1.status_code == 201

        # Second application attempt
        res2 = client.post("/api/applications/one-click", json=payload, headers=headers)
        assert res2.status_code == 409
        assert "already applied" in res2.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_withdraw_application(db_session):
    owner = _create_user(db_session, email="owner3@devlink.io", username="projowner3")
    applicant = _create_user(db_session, email="applicant3@devlink.io", username="applicantuser3")
    project = _create_project(db_session, owner=owner, title="Withdraw Test Project")

    def override_get_database():
        return db_session

    def override_get_current_user():
        return applicant

    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)
        headers = {"Origin": "http://localhost:3000"}

        payload = {
            "project_id": str(project.id),
            "cover_letter": "Application to be withdrawn",
        }

        res_apply = client.post("/api/applications/one-click", json=payload, headers=headers)
        assert res_apply.status_code == 201
        app_id = res_apply.json()["id"]

        res_withdraw = client.post(f"/api/applications/{app_id}/withdraw", headers=headers)
        assert res_withdraw.status_code == 200
        assert res_withdraw.json()["status"] == "withdrawn"
    finally:
        app.dependency_overrides.clear()
