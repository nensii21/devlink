from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


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
            "password": "Vermilion-Kestrel97!",
        },
    )
    r = client.post(
        "/api/auth/login", json={"email": email, "password": "Vermilion-Kestrel97!"}
    )
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


def test_auto_slug_generation_and_lookup():
    client = TestClient(app)
    owner_id, owner_token = _register_and_login(client, "slugowner@x.com", "slugowner")
    headers = {"Authorization": f"Bearer {owner_token}"}

    # Create org without providing slug
    res = client.post(
        "/organizations/",
        json={
            "name": "DevLink Labs",
            "organization_type": "startup",
        },
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["slug"] == "devlink-labs"

    # Lookup by generated slug
    lookup_res = client.get("/organizations/slug/devlink-labs")
    assert lookup_res.status_code == 200
    assert lookup_res.json()["id"] == data["id"]
    assert lookup_res.json()["name"] == "DevLink Labs"


def test_slug_collision_handling():
    client = TestClient(app)
    owner_id, owner_token = _register_and_login(client, "colowner@x.com", "colowner")
    headers = {"Authorization": f"Bearer {owner_token}"}

    # Create 3 organizations with names that generate colliding base slugs
    res1 = client.post(
        "/organizations/",
        json={"name": "DevLink Labs", "organization_type": "startup"},
        headers=headers,
    )
    res2 = client.post(
        "/organizations/",
        json={"name": "DevLink-Labs", "organization_type": "company"},
        headers=headers,
    )
    res3 = client.post(
        "/organizations/",
        json={"name": "DevLink _ Labs", "organization_type": "community"},
        headers=headers,
    )

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res3.status_code == 201

    assert res1.json()["slug"] == "devlink-labs"
    assert res2.json()["slug"] == "devlink-labs-1"
    assert res3.json()["slug"] == "devlink-labs-2"


def test_check_slug_availability():
    client = TestClient(app)
    owner_id, owner_token = _register_and_login(
        client, "checkowner@x.com", "checkowner"
    )
    headers = {"Authorization": f"Bearer {owner_token}"}

    # Available check before creation
    check_before = client.get("/organizations/check-slug/unique-org-slug")
    assert check_before.status_code == 200
    assert check_before.json() == {"slug": "unique-org-slug", "available": True}

    # Create org with custom slug
    res = client.post(
        "/organizations/",
        json={
            "name": "Unique Org",
            "slug": "unique-org-slug",
            "organization_type": "startup",
        },
        headers=headers,
    )
    assert res.status_code == 201

    # Check availability after creation
    check_after = client.get("/organizations/check-slug/unique-org-slug")
    assert check_after.status_code == 200
    assert check_after.json() == {"slug": "unique-org-slug", "available": False}
