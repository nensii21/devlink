import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.user import User
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
        first_name="Test",
        last_name="User",
        password_hash="fakehash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_update_user_profile_success():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, "profile_edit@example.com", "profile_edit_user")
    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "first_name": "Jane",
        "last_name": "Smith",
        "bio": "Full Stack Engineer building great web apps.",
        "location": "San Francisco, CA",
        "website": "https://janesmith.dev",
        "role": "Senior Engineer",
        "skills": ["React", "Python", "FastAPI"],
    }

    response = client.put("/api/users/me", headers=headers, json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"
    assert data["bio"] == "Full Stack Engineer building great web apps."
    assert data["location"] == "San Francisco, CA"
    assert "janesmith.dev" in data["website"]
    assert data["role"] == "Senior Engineer"
    assert "React" in data["skills"]
    assert "Python" in data["skills"]


def test_update_username_conflict():
    client = TestClient(app)
    db = TestingSessionLocal()
    user1 = _create_user(db, "u1@example.com", "user_one")
    user2 = _create_user(db, "u2@example.com", "user_two")

    token1 = create_access_token(str(user1.id))
    headers = {"Authorization": f"Bearer {token1}"}

    response = client.put("/api/users/me", headers=headers, json={"username": "user_two"})
    assert response.status_code == 400
    assert "Username is already taken" in response.json()["detail"]


def test_update_username_success():
    client = TestClient(app)
    db = TestingSessionLocal()
    user = _create_user(db, "u3@example.com", "old_username")
    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put("/api/users/me", headers=headers, json={"username": "new_username"})
    assert response.status_code == 200
    assert response.json()["username"] == "new_username"
