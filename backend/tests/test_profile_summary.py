from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.services.profile_summary_service import ProfileSummaryService


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_generate_profile_summary(client: TestClient, register_and_login, db):
    user_id, token = register_and_login(
        "profile_summary@example.com", "profile_summary"
    )

    response = client.post(
        "/api/profile-summary",
        json={"user_id": user_id},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user_id"] == user_id
    assert data["user_name"]
    assert data["summary"]
    assert len(data["summary"]) <= 500


def test_generate_profile_summary_uses_default_when_openai_unavailable(
    client: TestClient, register_and_login, db, monkeypatch
):
    user_id, token = register_and_login(
        "profile_summary_fb@example.com", "profile_summary_fb"
    )

    monkeypatch.setattr(
        ProfileSummaryService,
        "generate_summary",
        staticmethod(lambda db, user, stats=None: "Default fallback summary."),
    )

    response = client.post(
        "/api/profile-summary",
        json={"user_id": user_id},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200, response.text
    assert response.json()["summary"] == "Default fallback summary."


def test_generate_profile_summary_unknown_user_returns_404(
    client: TestClient, register_and_login
):
    _, token = register_and_login(
        "profile_summary_404@example.com", "profile_summary_404"
    )

    response = client.post(
        "/api/profile-summary",
        json={"user_id": str(uuid.uuid4())},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


def test_generate_profile_summary_requires_auth(client: TestClient):
    response = client.post(
        "/api/profile-summary",
        json={"user_id": str(uuid.uuid4())},
    )

    assert response.status_code in (401, 403)
