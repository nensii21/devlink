from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.main import app


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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


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


def test_follow_creates_notification():
    client = TestClient(app)
    a_id, a_tok = _register_and_login(client, "a@x.com", "alice")
    b_id, b_tok = _register_and_login(client, "b@x.com", "bob")

    r = client.post(f"/followers/{a_id}", headers={"Authorization": f"Bearer {b_tok}"})
    assert r.status_code == 201

    notifs = client.get(
        "/api/notifications/", headers={"Authorization": f"Bearer {a_tok}"}
    ).json()
    assert any(n["type"] == "follow" for n in notifs)

    b_notifs = client.get(
        "/api/notifications/", headers={"Authorization": f"Bearer {b_tok}"}
    ).json()
    assert all(n["type"] != "follow" for n in b_notifs)


def test_no_self_notification():
    client = TestClient(app)
    a_id, a_tok = _register_and_login(client, "c@x.com", "charlie")

    r = client.post(f"/followers/{a_id}", headers={"Authorization": f"Bearer {a_tok}"})
    assert r.status_code == 400


def test_notify_returns_none_when_recipient_is_sender():
    from app.services.notification_service import NotificationService
    from app.models.notification import NotificationType

    db = TestingSessionLocal()
    result = NotificationService.notify(
        db,
        recipient_id="00000000-0000-0000-0000-000000000001",
        sender_id="00000000-0000-0000-0000-000000000001",
        type=NotificationType.FOLLOW,
        title="Self test",
        message="Should not be created.",
    )
    assert result is None
    db.close()
