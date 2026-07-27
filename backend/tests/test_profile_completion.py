from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.skill import Skill
from app.models.user_skill import UserSkill

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_database] = override_get_db
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def _register_and_login(
    client: TestClient, email: str, username: str
) -> tuple[str, str]:
    client.post(
        "/api/auth/register",
        json={
            "first_name": username.capitalize(),
            "last_name": "User",
            "email": email,
            "username": username,
            "password": "Passw0rd!",
        },
    )
    r = client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"})
    token = r.json()["access_token"]
    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    return me.json()["id"], token


def test_empty_profile_completion():
    client = TestClient(app)
    user_id, token = _register_and_login(client, "emptyprof@x.com", "emptyprof")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/users/me/completion", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["completion"] == 0
    assert set(data["missing"]) == {
        "Avatar",
        "Bio",
        "Skills",
        "Experience",
        "GitHub",
        "Portfolio",
        "Location",
    }


def test_partially_completed_profile():
    client = TestClient(app)
    user_id, token = _register_and_login(client, "partialprof@x.com", "partialprof")
    headers = {"Authorization": f"Bearer {token}"}

    # Update 4 out of 7 factors (Bio, Location, GitHub, Experience)
    update_res = client.put(
        "/api/users/me",
        json={
            "bio": "Full stack developer interested in AI.",
            "location": "San Francisco, CA",
            "github_url": "https://github.com/partialprof",
            "experience_level": "Senior",
        },
        headers=headers,
    )
    assert update_res.status_code == 200

    res = client.get("/api/users/me/completion", headers=headers)
    assert res.status_code == 200
    data = res.json()
    # 4/7 factors completed = round(4/7 * 100) = 57%
    assert data["completion"] == 57
    assert set(data["missing"]) == {"Avatar", "Skills", "Portfolio"}


def test_fully_completed_profile():
    client = TestClient(app)
    user_id, token = _register_and_login(client, "fullprof@x.com", "fullprof")
    headers = {"Authorization": f"Bearer {token}"}

    # Add a skill directly in DB session
    db = TestingSessionLocal()
    skill = Skill(name="Python", normalized_name="python", slug="python")
    db.add(skill)
    db.flush()
    user_skill = UserSkill(user_id=uuid.UUID(user_id), skill_id=skill.id)
    db.add(user_skill)
    db.commit()

    # Update user profile with remaining factors
    from app.models.user import User as UserModel

    user_model = db.get(UserModel, uuid.UUID(user_id))

    user_model.profile_image = "https://example.com/avatar.jpg"
    user_model.bio = "Senior Backend Engineer"
    user_model.experience_level = "Senior"
    user_model.github_url = "https://github.com/fullprof"
    user_model.portfolio_url = "https://fullprof.dev"
    user_model.location = "New York, NY"
    db.commit()
    db.close()

    res = client.get("/api/users/me/completion", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["completion"] == 100
    assert data["missing"] == []


def test_get_user_completion_by_id():
    client = TestClient(app)
    user_id, token = _register_and_login(client, "byid@x.com", "byiduser")

    res = client.get(f"/api/users/{user_id}/completion")
    assert res.status_code == 200
    data = res.json()
    assert "completion" in data
    assert "missing" in data


def test_get_completion_user_not_found():
    client = TestClient(app)
    fake_id = uuid.uuid4()
    res = client.get(f"/api/users/{fake_id}/completion")
    assert res.status_code == 404
