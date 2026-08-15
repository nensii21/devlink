import pytest
from app.models.user import User
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def override_microsoft_config(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.settings.MICROSOFT_CLIENT_ID", "test_client_id"
    )
    monkeypatch.setattr(
        "app.core.config.settings.MICROSOFT_CLIENT_SECRET", "test_client_secret"
    )


def test_microsoft_login_success_new_user(
    client: TestClient, db, override_microsoft_config
):
    # Mock token exchange
    mock_post = AsyncMock()
    mock_response_token = MagicMock()
    mock_response_token.status_code = 200
    mock_response_token.json.return_value = {"access_token": "mocked_ms_token"}
    mock_post.return_value = mock_response_token

    # Mock user profile from Graph API
    mock_get = AsyncMock()
    mock_response_user = MagicMock()
    mock_response_user.status_code = 200
    mock_response_user.json.return_value = {
        "id": "ms_id_12345",
        "displayName": "Microsoft User",
        "userPrincipalName": "msuser@example.com",
    }
    mock_get.return_value = mock_response_user

    with patch("httpx.AsyncClient.post", new=mock_post):
        with patch("httpx.AsyncClient.get", new=mock_get):
            # We need to mock redis state checking
            with patch(
                "app.routers.auth.oauth_redis.get", new_callable=AsyncMock
            ) as mock_redis_get:
                mock_redis_get.return_value = "1"
                with patch(
                    "app.routers.auth.oauth_redis.delete", new_callable=AsyncMock
                ):
                    response = client.post(
                        "/api/auth/microsoft",
                        json={"code": "test_code_123", "state": "test_state"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "access_token" in data
                    assert data["user"]["email"] == "msuser@example.com"
                    assert data["user"]["first_name"] == "Microsoft"

                    # Verify DB state
                    user = (
                        db.query(User)
                        .filter(User.email == "msuser@example.com")
                        .first()
                    )
                    assert user is not None
                    assert user.microsoft_id == "ms_id_12345"
                    assert user.is_verified is True


def test_microsoft_login_link_existing_account(
    client: TestClient, db, override_microsoft_config
):
    # Pre-create a user with the same email but no microsoft_id
    from app.core.security import hash_password

    existing_user = User(
        first_name="Existing",
        last_name="User",
        username="ms_existing",
        email="msexisting@example.com",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db.add(existing_user)
    db.commit()
    db.refresh(existing_user)

    mock_post = AsyncMock()
    mock_response_token = MagicMock()
    mock_response_token.status_code = 200
    mock_response_token.json.return_value = {"access_token": "mocked_ms_token"}
    mock_post.return_value = mock_response_token

    mock_get = AsyncMock()
    mock_response_user = MagicMock()
    mock_response_user.status_code = 200
    mock_response_user.json.return_value = {
        "id": "ms_id_67890",
        "displayName": "Existing User MS",
        "userPrincipalName": "msexisting@example.com",
    }
    mock_get.return_value = mock_response_user

    with patch("httpx.AsyncClient.post", new=mock_post):
        with patch("httpx.AsyncClient.get", new=mock_get):
            with patch(
                "app.routers.auth.oauth_redis.get", new_callable=AsyncMock
            ) as mock_redis_get:
                mock_redis_get.return_value = "1"
                with patch(
                    "app.routers.auth.oauth_redis.delete", new_callable=AsyncMock
                ):
                    response = client.post(
                        "/api/auth/microsoft",
                        json={"code": "test_code_456", "state": "valid_state"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["user"]["email"] == "msexisting@example.com"
                    assert (
                        data["user"]["username"] == "ms_existing"
                    )  # Keeps original username

                    # Verify DB state
                    db.expire_all()
                    user = (
                        db.query(User)
                        .filter(User.email == "msexisting@example.com")
                        .first()
                    )
                    assert user.microsoft_id == "ms_id_67890"


def test_microsoft_login_invalid_code(client: TestClient, override_microsoft_config):
    mock_post = AsyncMock()
    mock_response_token = MagicMock()
    mock_response_token.status_code = 400
    mock_response_token.json.return_value = {
        "error": "invalid_grant",
        "error_description": "The provided value for the input parameter 'code' is not valid.",
    }
    mock_post.return_value = mock_response_token

    with patch("httpx.AsyncClient.post", new=mock_post):
        with patch(
            "app.routers.auth.oauth_redis.get", new_callable=AsyncMock
        ) as mock_redis_get:
            mock_redis_get.return_value = "1"
            with patch("app.routers.auth.oauth_redis.delete", new_callable=AsyncMock):
                response = client.post(
                    "/api/auth/microsoft",
                    json={"code": "invalid_code", "state": "test_state"},
                )
                assert response.status_code == 401
                assert "not valid" in response.json()["detail"]


def test_microsoft_login_invalid_state(client: TestClient, override_microsoft_config):
    with patch(
        "app.routers.auth.oauth_redis.get", new_callable=AsyncMock
    ) as mock_redis_get:
        # State not found in redis
        mock_redis_get.return_value = None
        response = client.post(
            "/api/auth/microsoft", json={"code": "some_code", "state": "invalid_state"}
        )
        assert response.status_code == 400
        assert "Invalid or expired OAuth state" in response.json()["detail"]
