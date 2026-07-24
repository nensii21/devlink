import pytest
import uuid
from fastapi.testclient import TestClient


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


def test_create_user(client: TestClient):
    response = client.post(
        "/api/users/",
        json={
            "first_name": "Create",
            "last_name": "User",
            "email": "createuser@example.com",
            "username": "createuser",
            "password": "Password123!",
        },
    )
    assert response.status_code == 201
    assert response.json()["username"] == "createuser"


def test_create_user_duplicate_email(client: TestClient, register_and_login):
    register_and_login("dupem@example.com", "dupem1")
    response = client.post(
        "/api/users/",
        json={
            "first_name": "Dup",
            "last_name": "User",
            "email": "dupem@example.com",
            "username": "dupem2",
            "password": "Password123!",
        },
    )
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_create_user_duplicate_username(client: TestClient, register_and_login):
    register_and_login("dupusr1@example.com", "dupusr")
    response = client.post(
        "/api/users/",
        json={
            "first_name": "Dup",
            "last_name": "User",
            "email": "dupusr2@example.com",
            "username": "dupusr",
            "password": "Password123!",
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


def test_activate_user(client: TestClient, register_and_login):
    uid, _ = register_and_login("act@example.com", "actuser")
    # Deactivate first
    client.patch(f"/api/users/{uid}/deactivate")

    response = client.patch(f"/api/users/{uid}/activate")
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_activate_user_not_found(client: TestClient):
    response = client.patch(f"/api/users/{uuid.uuid4()}/activate")
    assert response.status_code == 404


def test_deactivate_user(client: TestClient, register_and_login):
    uid, _ = register_and_login("deact@example.com", "deactuser")
    response = client.patch(f"/api/users/{uid}/deactivate")
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_deactivate_user_not_found(client: TestClient):
    response = client.patch(f"/api/users/{uuid.uuid4()}/deactivate")
    assert response.status_code == 404


def test_verify_user(client: TestClient, register_and_login):
    uid, _ = register_and_login("ver@example.com", "veruser")
    response = client.patch(f"/api/users/{uid}/verify")
    assert response.status_code == 200
    assert response.json()["is_verified"] is True


def test_verify_user_not_found(client: TestClient):
    response = client.patch(f"/api/users/{uuid.uuid4()}/verify")
    assert response.status_code == 404
