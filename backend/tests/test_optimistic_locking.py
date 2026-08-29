import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStage, ProjectVisibility
from app.models.user import User
from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService
from app.services.user_service import UserService


def test_project_optimistic_locking_success(client: TestClient, register_and_login):
    owner_id, token = register_and_login(
        "opt_project_owner@example.com", "optprojowner"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create project
    create_resp = client.post(
        "/api/projects/",
        json={
            "title": "Optimistic Locking Test Project",
            "slug": f"opt-lock-proj-{uuid.uuid4().hex[:6]}",
            "description": "Testing version increments and conflict detection.",
            "status": "active",
            "visibility": "public",
            "allow_duplicate": True,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    proj_data = create_resp.json()
    proj_id = proj_data["id"]
    assert proj_data.get("version") == 1

    # 2. Update project with matching version=1 -> version becomes 2
    update_resp1 = client.put(
        f"/api/projects/{proj_id}",
        json={"tagline": "First update with version 1", "version": 1},
        headers=headers,
    )
    assert update_resp1.status_code == 200
    assert update_resp1.json()["version"] == 2
    assert update_resp1.json()["tagline"] == "First update with version 1"

    # 3. Update project without explicit version -> version becomes 3
    update_resp2 = client.put(
        f"/api/projects/{proj_id}",
        json={"tagline": "Second update without explicit version"},
        headers=headers,
    )
    assert update_resp2.status_code == 200
    assert update_resp2.json()["version"] == 3


def test_project_optimistic_locking_conflict(client: TestClient, register_and_login):
    owner_id, token = register_and_login(
        "opt_conflict_owner@example.com", "optconfowner"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create project
    create_resp = client.post(
        "/api/projects/",
        json={
            "title": "Optimistic Conflict Project",
            "slug": f"opt-conflict-{uuid.uuid4().hex[:6]}",
            "description": "Testing concurrent modification conflict.",
            "status": "active",
            "visibility": "public",
            "allow_duplicate": True,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    proj_id = create_resp.json()["id"]

    # 2. First update succeeds (version -> 2)
    upd1 = client.put(
        f"/api/projects/{proj_id}",
        json={"tagline": "User A update", "version": 1},
        headers=headers,
    )
    assert upd1.status_code == 200
    assert upd1.json()["version"] == 2

    # 3. Second update with stale version=1 returns 409 Conflict
    upd_stale = client.put(
        f"/api/projects/{proj_id}",
        json={"tagline": "User B stale update", "version": 1},
        headers=headers,
    )
    assert upd_stale.status_code == 409
    assert "Version conflict" in upd_stale.json()["detail"]


def test_user_profile_optimistic_locking_success(
    client: TestClient, register_and_login
):
    user_id, token = register_and_login(
        "opt_user_success@example.com", "optusersuccess"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get initial profile -> version 1
    me_resp = client.get("/api/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["version"] == 1

    # 2. Update profile with matching version=1 -> version becomes 2
    upd1 = client.put(
        "/api/users/me",
        json={"headline": "Updated Headline V1", "version": 1},
        headers=headers,
    )
    assert upd1.status_code == 200
    assert upd1.json()["version"] == 2
    assert upd1.json()["headline"] == "Updated Headline V1"


def test_user_profile_optimistic_locking_conflict(
    client: TestClient, register_and_login
):
    user_id, token = register_and_login(
        "opt_user_conflict@example.com", "optuserconflict"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. First update succeeds (version 1 -> 2)
    upd1 = client.put(
        "/api/users/me",
        json={"headline": "Device A Update", "version": 1},
        headers=headers,
    )
    assert upd1.status_code == 200
    assert upd1.json()["version"] == 2

    # 2. Stale update with version 1 returns 409 Conflict
    upd_stale = client.put(
        "/api/users/me",
        json={"headline": "Device B Stale Update", "version": 1},
        headers=headers,
    )
    assert upd_stale.status_code == 409
    assert "Version conflict" in upd_stale.json()["detail"]
