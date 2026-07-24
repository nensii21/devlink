from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.user import User
from fastapi.testclient import TestClient


@pytest.fixture
def override_github_config(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.GITHUB_CLIENT_ID", "test_client_id")
    monkeypatch.setattr(
        "app.core.config.settings.GITHUB_CLIENT_SECRET", "test_client_secret"
    )


def test_github_login_success_new_user(
    client: TestClient, db, override_github_config
):
    # Mock token exchange
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "mocked_github_token"}
    mock_post.return_value = mock_response

    # Mock user profile and emails
    mock_get = AsyncMock()

    # Side effect: first call is to /user, second is to /user/emails
    def get_side_effect(url, *args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        if url == "https://api.github.com/user":
            mock_response.json.return_value = {
                "id": 1234567,
                "login": "new_octocat",
                "name": "Octo Cat",
                "html_url": "https://github.com/new_octocat",
                "avatar_url": "https://github.com/avatar.png",
            }
        elif url == "https://api.github.com/user/emails":
            mock_response.json.return_value = [
                {"email": "octocat@example.com", "primary": True, "verified": True}
            ]
        return mock_response

    mock_get.side_effect = get_side_effect

    with patch("httpx.AsyncClient.post", new=mock_post):
        with patch("httpx.AsyncClient.get", new=mock_get):
            response = client.post("/api/auth/github", json={"code": "test_code_123"})

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["user"]["email"] == "octocat@example.com"
            assert data["user"]["username"] == "new_octocat"

            # Verify DB state
            user = db.query(User).filter(User.email == "octocat@example.com").first()
            assert user is not None
            assert user.github_id == "1234567"
            assert user.is_verified is True


def test_github_login_link_existing_account(
    client: TestClient, db, override_github_config
):
    # Pre-create a user with the same email but no github_id
    from app.core.security import hash_password

    existing_user = User(
        first_name="Existing",
        last_name="User",
        username="existing_user",
        email="existing@example.com",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db.add(existing_user)
    db.commit()
    db.refresh(existing_user)

    # Mock token exchange
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "mocked_github_token"}
    mock_post.return_value = mock_response

    mock_get = AsyncMock()

    def get_side_effect(url, *args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        if url == "https://api.github.com/user":
            mock_response.json.return_value = {
                "id": 987654,
                "login": "existing_github",
                "name": "Existing User",
                "html_url": "https://github.com/existing_github",
                "avatar_url": "https://github.com/avatar2.png",
            }
        elif url == "https://api.github.com/user/emails":
            mock_response.json.return_value = [
                {"email": "existing@example.com", "primary": True, "verified": True}
            ]
        return mock_response

    mock_get.side_effect = get_side_effect

    with patch("httpx.AsyncClient.post", new=mock_post):
        with patch("httpx.AsyncClient.get", new=mock_get):
            response = client.post("/api/auth/github", json={"code": "test_code_456"})

            assert response.status_code == 200
            data = response.json()
            assert data["user"]["email"] == "existing@example.com"
            assert (
                data["user"]["username"] == "existing_user"
            )  # Keeps original username

            # Verify DB state
            db.expire_all()
            user = (
                db.query(User).filter(User.email == "existing@example.com").first()
            )
            assert user.github_id == "987654"
            assert user.profile_image == "https://github.com/avatar2.png"


def test_github_login_invalid_code(client: TestClient, override_github_config):
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "error": "bad_verification_code",
        "error_description": "The code passed is incorrect or expired.",
    }
    mock_post.return_value = mock_response

    with patch("httpx.AsyncClient.post", new=mock_post):
        response = client.post("/api/auth/github", json={"code": "invalid_code"})

        assert response.status_code == 401
        assert "incorrect or expired" in response.json()["detail"]
