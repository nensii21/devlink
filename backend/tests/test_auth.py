import pytest
from fastapi.testclient import TestClient


def test_register_success(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "testregister@example.com",
            "username": "testregister",
            "password": "Password123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testregister@example.com"
    assert data["username"] == "testregister"


def test_register_duplicate_email(client: TestClient, register_and_login):
    register_and_login("dup@example.com", "dupuser")
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Dup",
            "last_name": "User",
            "email": "dup@example.com",
            "username": "dupuser2",
            "password": "Password123!",
        },
    )
    assert response.status_code == 409
    assert "Email already exists" in response.json()["detail"]


def test_login_success(client: TestClient, register_and_login):
    # This also implicitly tests login since the fixture uses it,
    # but we will test it explicitly
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Login",
            "last_name": "User",
            "email": "login@example.com",
            "username": "loginuser",
            "password": "Password123!",
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "Password123!"},
    )
    assert response.status_code == 401


def test_me(client: TestClient, register_and_login):
    user_id, token = register_and_login("me@example.com", "meuser")
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_refresh_token(client: TestClient, register_and_login):
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Refresh",
            "last_name": "User",
            "email": "refresh@example.com",
            "username": "refreshuser",
            "password": "Password123!",
        },
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "refresh@example.com", "password": "Password123!"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()


def test_refresh_invalid_token(client: TestClient):
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401


def test_logout(client: TestClient, register_and_login):
    user_id, token = register_and_login("logout@example.com", "logoutuser")
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_change_password(client: TestClient, register_and_login):
    user_id, token = register_and_login("cp@example.com", "cpuser", "OldPass1!")
    response = client.patch(
        "/api/auth/change-password",
        json={"current_password": "OldPass1!", "new_password": "NewPass2!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Check if old password fails
    login_old = client.post(
        "/api/auth/login", json={"email": "cp@example.com", "password": "OldPass1!"}
    )
    assert login_old.status_code == 401

    # Check if new password works
    login_new = client.post(
        "/api/auth/login", json={"email": "cp@example.com", "password": "NewPass2!"}
    )
    assert login_new.status_code == 200


def test_change_password_wrong_current(client: TestClient, register_and_login):
    user_id, token = register_and_login("cp2@example.com", "cpuser2", "OldPass1!")
    response = client.patch(
        "/api/auth/change-password",
        json={"current_password": "WrongOld!", "new_password": "NewPass2!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_forgot_password(client: TestClient, register_and_login):
    register_and_login("forgot@example.com", "forgotuser")
    response = client.post(
        "/api/auth/forgot-password", json={"email": "forgot@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_reset_password(client: TestClient, register_and_login):
    user_id, _ = register_and_login("reset@example.com", "resetuser", "OldPass1!")
    forgot = client.post(
        "/api/auth/forgot-password", json={"email": "reset@example.com"}
    )

    from app.core.security import _create_token
    from datetime import timedelta

    reset_token = _create_token(str(user_id), timedelta(hours=1), "reset")

    response = client.post(
        "/api/auth/reset-password",
        json={"token": reset_token, "new_password": "BrandNewPass1!"},
    )
    assert response.status_code == 200

    login_resp = client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "BrandNewPass1!"},
    )
    assert login_resp.status_code == 200


def test_resend_verification(client: TestClient, register_and_login):
    register_and_login("verify@example.com", "verifyuser")
    response = client.post(
        "/api/auth/resend-verification", json={"email": "verify@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_resend_verification_nonexistent(client: TestClient):
    response = client.post(
        "/api/auth/resend-verification", json={"email": "nonexistent@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True  # Fails silently for security
