from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.user import User

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


# ==================== Helper ====================
def _register_and_login(client: TestClient, email: str, username: str) -> tuple[str, str]:
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Test",
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


# ==================== Tests ====================
def test_last_seen_updated_on_login():
    client = TestClient(app)
    user_id, token = _register_and_login(client, "test@devlink.com", "testuser")

    db = TestingSessionLocal()
    user = db.get(User, uuid.UUID(user_id))
    assert user.last_seen is not None
    db.close()


def test_last_seen_updated_on_authenticated_requests_with_throttling():
    client = TestClient(app)
    user_id, token = _register_and_login(client, "test@devlink.com", "testuser")

    db = TestingSessionLocal()
    user = db.get(User, uuid.UUID(user_id))
    first_seen = user.last_seen
    assert first_seen is not None

    client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    db.refresh(user)
    assert user.last_seen == first_seen

    user.last_seen = datetime.now(timezone.utc) - timedelta(seconds=70)
    db.commit()
    throttled_seen = user.last_seen

    client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    db.refresh(user)
    assert user.last_seen > throttled_seen
    db.close()


def test_is_online_status_and_custom_thresholds():
    client = TestClient(app)
    user_id, token = _register_and_login(client, "test@devlink.com", "testuser")

    r = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    data = r.json()
    assert data["is_online"] is True
    assert data["last_seen"] is not None

    r2 = client.get(f"/api/users/{user_id}")
    assert r2.json()["is_online"] is True

    db = TestingSessionLocal()
    user = db.get(User, uuid.UUID(user_id))
    user.last_seen = datetime.now(timezone.utc) - timedelta(minutes=10)
    db.commit()
    db.close()

    r3 = client.get(f"/api/users/{user_id}")
    assert r3.json()["is_online"] is False

    r4 = client.get(f"/api/users/{user_id}?online_threshold=1200")
    assert r4.json()["is_online"] is True

    r5 = client.get("/api/users/?online_threshold=1200")
    users = r5.json()
    assert len(users) > 0
    assert any(u["id"] == user_id and u["is_online"] is True for u in users)

    # Check on list users endpoint with small threshold (e.g. 5 seconds) -> should show offline
    r6 = client.get("/api/users/?online_threshold=5")
    users_offline = r6.json()
    assert any(u["id"] == user_id and u["is_online"] is False for u in users_offline)
