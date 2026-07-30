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
from app.models.refresh_token import RefreshToken

from tests.conftest import TestingSessionLocal


def _register_user(client: TestClient, email: str, username: str):
    return client.post(
        "/api/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "username": username,
            "password": "Password123!",
        },
    )


def test_login_creates_refresh_token_in_db():
    client = TestClient(app)
    _register_user(client, "login_test@example.com", "logintestuser")

    res = client.post(
        "/api/auth/login",
        json={"email": "login_test@example.com", "password": "Password123!"},
        headers={"User-Agent": "Pytest-Client"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # Verify session in DB
    db = TestingSessionLocal()
    tokens = db.query(RefreshToken).all()
    assert len(tokens) >= 1
    assert tokens[-1].is_revoked is False
    db.close()


def test_refresh_token_rotation():
    client = TestClient(app)
    _register_user(client, "rotate_test@example.com", "rotatetestuser")

    login_res = client.post(
        "/api/auth/login",
        json={"email": "rotate_test@example.com", "password": "Password123!"},
    )
    old_refresh_token = login_res.json()["refresh_token"]

    # Rotate token
    ref_res = client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    new_refresh_token = ref_data["refresh_token"]

    assert new_refresh_token != old_refresh_token

    # Verify old token is marked revoked in DB
    db = TestingSessionLocal()
    old_token_record = (
        db.query(RefreshToken).filter(RefreshToken.token == old_refresh_token).first()
    )
    assert old_token_record is not None
    assert old_token_record.is_revoked is True
    db.close()


def test_refresh_token_reuse_prevention():
    client = TestClient(app)
    _register_user(client, "reuse_test@example.com", "reusetestuser")

    login_res = client.post(
        "/api/auth/login",
        json={"email": "reuse_test@example.com", "password": "Password123!"},
    )
    initial_refresh_token = login_res.json()["refresh_token"]

    # Legitimate first refresh
    ref_res = client.post(
        "/api/auth/refresh",
        json={"refresh_token": initial_refresh_token},
    )
    assert ref_res.status_code == 200
    valid_new_token = ref_res.json()["refresh_token"]

    # Attacker/reused attempt with initial_refresh_token
    reuse_res = client.post(
        "/api/auth/refresh",
        json={"refresh_token": initial_refresh_token},
    )
    assert reuse_res.status_code == 401

    # Attempting to use even valid_new_token should now fail because reuse revoked ALL user tokens
    second_res = client.post(
        "/api/auth/refresh",
        json={"refresh_token": valid_new_token},
    )
    assert second_res.status_code == 401


def test_get_active_sessions():
    client = TestClient(app)
    _register_user(client, "sessions_test@example.com", "sessionstestuser")

    login_res = client.post(
        "/api/auth/login",
        json={"email": "sessions_test@example.com", "password": "Password123!"},
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    res = client.get("/api/auth/sessions", headers=headers)
    assert res.status_code == 200
    sessions = res.json()
    assert len(sessions) >= 1
    assert "id" in sessions[0]


def test_revoke_individual_session():
    client = TestClient(app)
    _register_user(client, "revonesess@example.com", "revonesessuser")

    login_res = client.post(
        "/api/auth/login",
        json={"email": "revonesess@example.com", "password": "Password123!"},
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    sessions_res = client.get("/api/auth/sessions", headers=headers)
    session_id = sessions_res.json()[0]["id"]

    del_res = client.delete(f"/api/auth/sessions/{session_id}", headers=headers)
    assert del_res.status_code == 200

    sessions_after = client.get("/api/auth/sessions", headers=headers).json()
    assert len(sessions_after) == 0


def test_revoke_all_sessions():
    client = TestClient(app)
    _register_user(client, "revall@example.com", "revalluser")

    login_res1 = client.post(
        "/api/auth/login",
        json={"email": "revall@example.com", "password": "Password123!"},
    )
    login_res2 = client.post(
        "/api/auth/login",
        json={"email": "revall@example.com", "password": "Password123!"},
    )
    access_token = login_res2.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Before revoke, 2 active sessions
    active_before = client.get("/api/auth/sessions", headers=headers).json()
    assert len(active_before) == 2

    # Logout all
    logout_all_res = client.post("/api/auth/logout-all", headers=headers)
    assert logout_all_res.status_code == 200

    # After logout all, 0 active sessions
    active_after = client.get("/api/auth/sessions", headers=headers).json()
    assert len(active_after) == 0
