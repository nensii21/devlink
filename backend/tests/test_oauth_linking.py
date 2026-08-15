import pytest
from uuid import uuid4

from app.models.user import User
from app.core.security import create_access_token, hash_password
from app.services.oauth_linking_service import OAuthLinkingService


@pytest.fixture
def user_with_password(db):
    user = User(
        id=uuid4(),
        first_name="OAuth",
        last_name="Tester",
        username=f"oauth_user_{uuid4().hex[:6]}",
        email=f"oauth_{uuid4().hex[:6]}@example.com",
        password_hash=hash_password("SecretPassword123!"),
        github_id="gh_123456",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def oauth_only_user(db):
    user = User(
        id=uuid4(),
        first_name="OAuthOnly",
        last_name="User",
        username=f"oauth_only_{uuid4().hex[:6]}",
        email=f"oauth_only_{uuid4().hex[:6]}@example.com",
        password_hash=None,
        google_id="google_999888",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_user(db):
    user = User(
        id=uuid4(),
        first_name="Other",
        last_name="User",
        username=f"other_user_{uuid4().hex[:6]}",
        email=f"other_{uuid4().hex[:6]}@example.com",
        password_hash=hash_password("OtherPassword123!"),
        gitlab_id="gitlab_777666",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers():
    def _headers(user):
        token = create_access_token(user_id=str(user.id))
        return {"Authorization": f"Bearer {token}"}

    return _headers


def test_get_linked_oauth_providers(client, user_with_password, auth_headers):
    res = client.get(
        "/api/v1/users/me/oauth-accounts",
        headers=auth_headers(user_with_password),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["has_password"] is True
    assert data["linked_count"] >= 1

    providers = {p["provider"]: p for p in data["providers"]}
    assert providers["github"]["is_linked"] is True
    assert providers["github"]["provider_user_id"] == "gh_123456"
    assert providers["google"]["is_linked"] is False


def test_link_oauth_account_success(client, user_with_password, auth_headers):
    res = client.post(
        "/api/v1/users/me/oauth-accounts/link",
        json={"provider": "google", "provider_user_id": "google_112233"},
        headers=auth_headers(user_with_password),
    )
    assert res.status_code == 200
    data = res.json()

    providers = {p["provider"]: p for p in data["providers"]}
    assert providers["google"]["is_linked"] is True
    assert providers["google"]["provider_user_id"] == "google_112233"


def test_link_oauth_account_duplicate_conflict(
    client, user_with_password, other_user, auth_headers
):
    # Attempt to link other_user's gitlab_id to user_with_password
    res = client.post(
        "/api/v1/users/me/oauth-accounts/link",
        json={"provider": "gitlab", "provider_user_id": "gitlab_777666"},
        headers=auth_headers(user_with_password),
    )
    assert res.status_code == 409
    assert "already linked to another DevLink user" in res.json()["detail"]


def test_unlink_oauth_account_success(client, user_with_password, auth_headers):
    res = client.post(
        "/api/v1/users/me/oauth-accounts/unlink",
        json={"provider": "github"},
        headers=auth_headers(user_with_password),
    )
    assert res.status_code == 200
    data = res.json()

    providers = {p["provider"]: p for p in data["providers"]}
    assert providers["github"]["is_linked"] is False


def test_unlink_oauth_account_sole_auth_prevention(
    client, oauth_only_user, auth_headers
):
    # Attempt to unlink google_id when user has no password and google is their only auth method
    res = client.post(
        "/api/v1/users/me/oauth-accounts/unlink",
        json={"provider": "google"},
        headers=auth_headers(oauth_only_user),
    )
    assert res.status_code == 400
    assert "only authentication method" in res.json()["detail"]


def test_unlink_oauth_account_with_second_provider(
    client, db, oauth_only_user, auth_headers
):
    # Link a second provider (github) first
    OAuthLinkingService.link_oauth_account(
        db, oauth_only_user, "github", "gh_secondary_123"
    )

    # Unlinking google should now succeed because github remains
    res = client.post(
        "/api/v1/users/me/oauth-accounts/unlink",
        json={"provider": "google"},
        headers=auth_headers(oauth_only_user),
    )
    assert res.status_code == 200
    data = res.json()

    providers = {p["provider"]: p for p in data["providers"]}
    assert providers["google"]["is_linked"] is False
    assert providers["github"]["is_linked"] is True
