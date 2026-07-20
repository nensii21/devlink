from __future__ import annotations

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.user import User
from app.models.organization import Organization, OrganizationType
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.services.organization_service import OrganizationService

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


def test_owner_can_update_organization():
    client = TestClient(app)
    owner_id, owner_token = _register_and_login(client, "owner@x.com", "owner")
    headers = {"Authorization": f"Bearer {owner_token}"}

    # Create organization
    org_resp = client.post(
        "/organizations/",
        json={
            "name": "Acme Corp",
            "slug": "acme",
            "organization_type": "startup",
        },
        headers=headers,
    )
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    # Update organization
    update_resp = client.put(
        f"/organizations/{org_id}",
        json={
            "description": "Updated Description",
        },
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Updated Description"


def test_non_owner_cannot_update_organization():
    client = TestClient(app)
    owner_id, owner_token = _register_and_login(client, "owner@x.com", "owner")
    other_id, other_token = _register_and_login(client, "other@x.com", "other")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Create organization
    org_resp = client.post(
        "/organizations/",
        json={
            "name": "Acme Corp",
            "slug": "acme",
            "organization_type": "startup",
        },
        headers=owner_headers,
    )
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    # Try updating as other user
    update_resp = client.put(
        f"/organizations/{org_id}",
        json={
            "description": "Updated Description",
        },
        headers=other_headers,
    )
    assert update_resp.status_code == 403
    assert "permission denied" in update_resp.json()["detail"].lower()


def test_owner_can_delete_organization():
    client = TestClient(app)
    owner_id, owner_token = _register_and_login(client, "owner@x.com", "owner")
    headers = {"Authorization": f"Bearer {owner_token}"}

    org_resp = client.post(
        "/organizations/",
        json={
            "name": "Acme Corp",
            "slug": "acme",
            "organization_type": "startup",
        },
        headers=headers,
    )
    org_id = org_resp.json()["id"]

    delete_resp = client.delete(
        f"/organizations/{org_id}",
        headers=headers,
    )
    assert delete_resp.status_code == 240 or delete_resp.status_code == 204

    # Verify it is deleted
    get_resp = client.get(f"/organizations/{org_id}")
    assert get_resp.status_code == 404


def test_non_owner_cannot_delete_organization():
    client = TestClient(app)
    owner_id, owner_token = _register_and_login(client, "owner@x.com", "owner")
    other_id, other_token = _register_and_login(client, "other@x.com", "other")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    org_resp = client.post(
        "/organizations/",
        json={
            "name": "Acme Corp",
            "slug": "acme",
            "organization_type": "startup",
        },
        headers=owner_headers,
    )
    org_id = org_resp.json()["id"]

    # Try deleting as other user
    delete_resp = client.delete(
        f"/organizations/{org_id}",
        headers=other_headers,
    )
    assert delete_resp.status_code == 403
    assert "permission denied" in delete_resp.json()["detail"].lower()


def test_owner_can_toggle_settings():
    client = TestClient(app)
    owner_id, owner_token = _register_and_login(client, "owner@x.com", "owner")
    headers = {"Authorization": f"Bearer {owner_token}"}

    org_resp = client.post(
        "/organizations/",
        json={
            "name": "Acme Corp",
            "slug": "acme",
            "organization_type": "startup",
        },
        headers=headers,
    )
    org_id = org_resp.json()["id"]

    # Verify, enable hiring, deactivate
    for action in ["verify", "enable-hiring", "deactivate"]:
        resp = client.patch(f"/organizations/{org_id}/{action}", headers=headers)
        assert resp.status_code == 200

    # Check status
    get_resp = client.get(f"/organizations/{org_id}")
    org_data = get_resp.json()
    assert org_data["verified"] is True
    assert org_data["hiring"] is True
    assert org_data["active"] is False


def test_non_owner_cannot_toggle_settings():
    client = TestClient(app)
    owner_id, owner_token = _register_and_login(client, "owner@x.com", "owner")
    other_id, other_token = _register_and_login(client, "other@x.com", "other")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    org_resp = client.post(
        "/organizations/",
        json={
            "name": "Acme Corp",
            "slug": "acme",
            "organization_type": "startup",
        },
        headers=owner_headers,
    )
    org_id = org_resp.json()["id"]

    # Try all endpoints as other user
    for action in [
        "verify",
        "enable-hiring",
        "disable-hiring",
        "activate",
        "deactivate",
    ]:
        resp = client.patch(f"/organizations/{org_id}/{action}", headers=other_headers)
        assert resp.status_code == 403
        assert "permission denied" in resp.json()["detail"].lower()
