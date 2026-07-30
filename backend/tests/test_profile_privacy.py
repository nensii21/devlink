from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User
from app.models.follower import Follower


@pytest.fixture
def privacy_users(db: Session):
    user1 = User(
        id=uuid.uuid4(),
        email="privacy_owner@example.com",
        username="privacy_owner",
        first_name="Privacy",
        last_name="Owner",
        password_hash="hashed_password",
        public_email="privacy_owner@example.com",
        github_url="https://github.com/privacyowner",
        resume_url="https://example.com/resume.pdf",
        linkedin_url="https://linkedin.com/in/privacyowner",
        website="https://privacyowner.dev",
        portfolio_url="https://portfolio.privacyowner.dev",
        availability=[
            {"day": "Monday", "start_time": "09:00:00", "end_time": "17:00:00"}
        ],
        is_active=True,
    )
    user2 = User(
        id=uuid.uuid4(),
        email="privacy_follower@example.com",
        username="privacy_follower",
        first_name="Privacy",
        last_name="Follower",
        password_hash="hashed_password",
        is_active=True,
    )
    user3 = User(
        id=uuid.uuid4(),
        email="privacy_stranger@example.com",
        username="privacy_stranger",
        first_name="Privacy",
        last_name="Stranger",
        password_hash="hashed_password",
        is_active=True,
    )
    db.add_all([user1, user2, user3])
    db.commit()

    # User2 follows User1
    follower = Follower(
        id=uuid.uuid4(),
        follower_id=user2.id,
        following_id=user1.id,
    )
    db.add(follower)
    db.commit()

    return user1, user2, user3


def test_get_default_privacy_settings(client: TestClient, privacy_users):
    owner, _, _ = privacy_users
    access_token = create_access_token(str(owner.id))
    headers = {"Authorization": f"Bearer {access_token}"}

    res = client.get("/api/users/me/privacy", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "private"
    assert data["github"] == "public"
    assert data["resume"] == "public"
    assert data["social_links"] == "public"
    assert data["availability"] == "public"


def test_update_privacy_settings(client: TestClient, privacy_users):
    owner, _, _ = privacy_users
    access_token = create_access_token(str(owner.id))
    headers = {"Authorization": f"Bearer {access_token}"}

    payload = {
        "email": "public",
        "github": "followers",
        "resume": "private",
        "social_links": "authenticated",
        "availability": "followers",
    }
    res = client.put("/api/users/me/privacy", json=payload, headers=headers)
    assert res.status_code == 200

    res_get = client.get("/api/users/me/privacy", headers=headers)
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["email"] == "public"
    assert data["github"] == "followers"
    assert data["resume"] == "private"
    assert data["social_links"] == "authenticated"
    assert data["availability"] == "followers"


def test_privacy_filtering_unauthenticated(client: TestClient, privacy_users):
    owner, _, _ = privacy_users

    # Default settings: email=private, github=public, resume=public, social_links=public, availability=public
    res = client.get(f"/api/users/{owner.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["public_email"] is None  # Private by default
    assert data["github_url"] == "https://github.com/privacyowner"
    assert data["resume_url"] == "https://example.com/resume.pdf"
    assert data["linkedin_url"] == "https://linkedin.com/in/privacyowner"
    assert len(data["availability"]) == 1


def test_privacy_filtering_follower_vs_stranger(client: TestClient, privacy_users):
    owner, follower_user, stranger_user = privacy_users
    owner_token = create_access_token(str(owner.id))

    # Set github=followers, resume=private, availability=followers
    update_payload = {
        "github": "followers",
        "resume": "private",
        "availability": "followers",
    }
    client.put(
        "/api/users/me/privacy",
        json=update_payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Stranger views profile
    stranger_token = create_access_token(str(stranger_user.id))
    res_stranger = client.get(
        f"/api/users/{owner.id}", headers={"Authorization": f"Bearer {stranger_token}"}
    )
    assert res_stranger.status_code == 200
    data_stranger = res_stranger.json()
    assert data_stranger["github_url"] is None  # followers only
    assert data_stranger["resume_url"] is None  # private
    assert len(data_stranger["availability"]) == 0  # followers only

    # Follower views profile
    follower_token = create_access_token(str(follower_user.id))
    res_follower = client.get(
        f"/api/users/{owner.id}", headers={"Authorization": f"Bearer {follower_token}"}
    )
    assert res_follower.status_code == 200
    data_follower = res_follower.json()
    assert data_follower["github_url"] == "https://github.com/privacyowner"
    assert data_follower["resume_url"] is None  # private
    assert len(data_follower["availability"]) == 1


def test_privacy_self_access(client: TestClient, privacy_users):
    owner, _, _ = privacy_users
    owner_token = create_access_token(str(owner.id))

    # Set all to private
    update_payload = {
        "email": "private",
        "github": "private",
        "resume": "private",
        "social_links": "private",
        "availability": "private",
    }
    client.put(
        "/api/users/me/privacy",
        json=update_payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Owner views own profile
    res = client.get(
        f"/api/users/{owner.id}", headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["public_email"] == "privacy_owner@example.com"
    assert data["github_url"] == "https://github.com/privacyowner"
    assert data["resume_url"] == "https://example.com/resume.pdf"
    assert data["linkedin_url"] == "https://linkedin.com/in/privacyowner"
    assert len(data["availability"]) == 1
