import uuid

from fastapi.testclient import TestClient

from app.models.user import User


def _promote_to_admin(db, user_id) -> None:
    """Give an already-registered user the system admin role.

    The administrative routes on this router are guarded by
    ``require_roles(SystemRole.ADMIN)``. There is no API for handing out that
    role, so tests set it directly -- the same thing a deployment does with a
    seed script.
    """
    user = db.get(User, uuid.UUID(str(user_id)))
    user.system_role = "admin"
    db.add(user)
    db.commit()


def _admin_headers(client: TestClient, register_and_login, db) -> dict[str, str]:
    """Register an administrator and return their auth header."""
    uid, token = register_and_login("root@example.com", "rootadmin")
    _promote_to_admin(db, uid)
    return {"Authorization": f"Bearer {token}"}


def test_check_username_available(client: TestClient):
    response = client.get("/api/users/check-username?username=newuser123")
    assert response.status_code == 200
    assert response.json()["available"] is True


def test_check_username_taken(client: TestClient, register_and_login):
    register_and_login("taken@example.com", "takenuser")
    response = client.get("/api/users/check-username?username=takenuser")
    assert response.status_code == 200
    assert response.json()["available"] is False


def test_check_username_invalid(client: TestClient):
    response = client.get("/api/users/check-username?username=a")  # too short
    assert response.status_code == 400


def test_create_user(client: TestClient, register_and_login, db):
    headers = _admin_headers(client, register_and_login, db)
    response = client.post(
        "/api/users/",
        headers=headers,
        json={
            "first_name": "Create",
            "last_name": "User",
            "email": "createuser@example.com",
            "username": "createuser",
            "password": "Vermilion-Kestrel97!",
        },
    )
    assert response.status_code == 201
    assert response.json()["username"] == "createuser"


def test_create_user_requires_authentication(client: TestClient):
    response = client.post(
        "/api/users/",
        json={
            "first_name": "Anon",
            "last_name": "User",
            "email": "anon@example.com",
            "username": "anonuser",
            "password": "Vermilion-Kestrel97!",
        },
    )
    assert response.status_code == 401


def test_create_user_rejects_non_admin(client: TestClient, register_and_login):
    _, token = register_and_login("plain@example.com", "plainuser")
    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "first_name": "Nope",
            "last_name": "User",
            "email": "nope@example.com",
            "username": "nopeuser",
            "password": "Vermilion-Kestrel97!",
        },
    )
    assert response.status_code == 403


def test_create_user_duplicate_email(client: TestClient, register_and_login, db):
    register_and_login("dupem@example.com", "dupem1")
    headers = _admin_headers(client, register_and_login, db)
    response = client.post(
        "/api/users/",
        headers=headers,
        json={
            "first_name": "Dup",
            "last_name": "User",
            "email": "dupem@example.com",
            "username": "dupem2",
            "password": "Vermilion-Kestrel97!",
        },
    )
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_create_user_duplicate_username(client: TestClient, register_and_login, db):
    register_and_login("dupusr1@example.com", "dupusr")
    headers = _admin_headers(client, register_and_login, db)
    response = client.post(
        "/api/users/",
        headers=headers,
        json={
            "first_name": "Dup",
            "last_name": "User",
            "email": "dupusr2@example.com",
            "username": "dupusr",
            "password": "Vermilion-Kestrel97!",
        },
    )
    assert response.status_code == 400
    assert "username" in response.json()["detail"].lower()


def test_get_me(client: TestClient, register_and_login):
    _, token = register_and_login("getme@example.com", "getme")
    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "getme"


def test_get_user(client: TestClient, register_and_login):
    uid, _ = register_and_login("getuid@example.com", "getuid")
    response = client.get(f"/api/users/{uid}")
    assert response.status_code == 200
    assert response.json()["username"] == "getuid"


def test_get_user_not_found(client: TestClient):
    response = client.get(f"/api/users/{uuid.uuid4()}")
    assert response.status_code == 404


def test_list_users(client: TestClient, register_and_login):
    register_and_login("list1@example.com", "list1")
    register_and_login("list2@example.com", "list2")
    response = client.get("/api/users/?skip=0&limit=10")
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_get_user_stats(client: TestClient, register_and_login):
    uid, _ = register_and_login("stats@example.com", "statsuser")
    response = client.get(f"/api/users/{uid}/stats")
    assert response.status_code == 200
    assert "projects" in response.json()


def test_get_user_stats_not_found(client: TestClient):
    response = client.get(f"/api/users/{uuid.uuid4()}/stats")
    assert response.status_code == 404


def test_update_me(client: TestClient, register_and_login):
    _, token = register_and_login("updme@example.com", "updme")
    response = client.put(
        "/api/users/me",
        json={"first_name": "UpdatedName", "bio": "New bio"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "UpdatedName"
    assert response.json()["bio"] == "New bio"


def test_delete_me(client: TestClient, register_and_login):
    _, token = register_and_login("delme@example.com", "delme")
    response = client.delete(
        "/api/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204

    # Verify user is gone
    me_resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 404


def test_activate_user(client: TestClient, register_and_login, db):
    uid, _ = register_and_login("act@example.com", "actuser")
    headers = _admin_headers(client, register_and_login, db)

    # Deactivate first
    client.patch(f"/api/users/{uid}/deactivate", headers=headers)

    response = client.patch(f"/api/users/{uid}/activate", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_activate_user_not_found(client: TestClient, register_and_login, db):
    headers = _admin_headers(client, register_and_login, db)
    response = client.patch(f"/api/users/{uuid.uuid4()}/activate", headers=headers)
    assert response.status_code == 404


def test_deactivate_user(client: TestClient, register_and_login, db):
    uid, _ = register_and_login("deact@example.com", "deactuser")
    headers = _admin_headers(client, register_and_login, db)

    response = client.patch(f"/api/users/{uid}/deactivate", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_deactivate_user_not_found(client: TestClient, register_and_login, db):
    headers = _admin_headers(client, register_and_login, db)
    response = client.patch(f"/api/users/{uuid.uuid4()}/deactivate", headers=headers)
    assert response.status_code == 404


def test_verify_user(client: TestClient, register_and_login, db):
    uid, _ = register_and_login("ver@example.com", "veruser")
    headers = _admin_headers(client, register_and_login, db)

    response = client.patch(f"/api/users/{uid}/verify", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_verified"] is True


def test_verify_user_not_found(client: TestClient, register_and_login, db):
    headers = _admin_headers(client, register_and_login, db)
    response = client.patch(f"/api/users/{uuid.uuid4()}/verify", headers=headers)
    assert response.status_code == 404


def test_get_me_unauthenticated(client: TestClient):
    res = client.get("/api/users/me")
    assert res.status_code == 401


def test_update_me_unauthenticated(client: TestClient):
    res = client.put("/api/users/me", json={"headline": "Test Headline"})
    assert res.status_code == 401


# `test_get_user_not_found` was declared a second time here, identical to the
# one earlier in this file apart from a local variable name. The later
# definition shadowed the earlier one.


def test_update_user_invalid_payload(client: TestClient, register_and_login):
    _, token = register_and_login("usr_inv_payload@example.com", "usrinvpayload")
    res = client.put(
        "/api/users/me",
        json={"website": "not-a-valid-url"},  # invalid URL pattern
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422
