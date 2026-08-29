from datetime import datetime, timezone, timedelta
import pytest
from fastapi import status
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.services.refresh_token_service import RefreshTokenService


def create_test_user(db, email="rotate_test@example.com", username="rotateuser"):
    user = User(
        first_name="Rotate",
        last_name="User",
        username=username,
        email=email,
        password_hash="hashed_password",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_refresh_token_rotation_success(client, db):
    user = create_test_user(db)
    refresh_token_str = create_refresh_token(str(user.id))
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Store refresh token in DB
    db_token = RefreshTokenService.create_token_for_user(
        db=db,
        user_id=user.id,
        token_str=refresh_token_str,
        expires_at=expires_at,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        ip_address="192.168.1.1",
    )
    db.commit()

    # Call refresh endpoint to rotate tokens
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token_str},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

    new_refresh_token_str = data["refresh_token"]

    # Verify original token is marked revoked
    db.refresh(db_token)
    assert db_token.is_revoked is True
    assert db_token.revoked_at is not None

    # Verify new token is stored in DB
    new_db_token = RefreshTokenService.get_token(db, new_refresh_token_str)
    assert new_db_token is not None
    assert new_db_token.is_revoked is False
    assert str(new_db_token.user_id) == str(user.id)


def test_revoked_token_reuse_protection(client, db):
    user = create_test_user(db)

    # Create two refresh tokens (e.g. two concurrent active devices)
    token_1_str = create_refresh_token(str(user.id))
    token_2_str = create_refresh_token(str(user.id))
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    db_token_1 = RefreshTokenService.create_token_for_user(
        db=db,
        user_id=user.id,
        token_str=token_1_str,
        expires_at=expires_at,
    )
    db_token_2 = RefreshTokenService.create_token_for_user(
        db=db,
        user_id=user.id,
        token_str=token_2_str,
        expires_at=expires_at,
    )

    # Revoke token_1 to simulate it already having been rotated/reused
    db_token_1.is_revoked = True
    db_token_1.revoked_at = datetime.now(timezone.utc)
    db.commit()

    # Re-use already revoked token_1 to refresh session
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": token_1_str},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "reused" in response.json()["detail"].lower()

    # Verify that security sweep revoked all active sessions for this user
    db.refresh(db_token_1)
    db.refresh(db_token_2)
    assert db_token_1.is_revoked is True
    assert db_token_2.is_revoked is True


def test_refresh_token_metadata_persisted(client, db):
    user = create_test_user(db)
    refresh_token_str = create_refresh_token(str(user.id))
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Store refresh token with metadata
    db_token = RefreshTokenService.create_token_for_user(
        db=db,
        user_id=user.id,
        token_str=refresh_token_str,
        expires_at=expires_at,
        user_agent="PostmanRuntime/7.29.2",
        ip_address="127.0.0.1",
    )
    db.commit()

    # Call refresh endpoint with headers
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token_str},
        headers={
            "User-Agent": "PostmanRuntime/7.29.2",
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    new_refresh_token_str = data["refresh_token"]

    # Verify metadata is correctly copied/assigned to new token record
    new_db_token = RefreshTokenService.get_token(db, new_refresh_token_str)
    assert new_db_token is not None
    assert new_db_token.user_agent == "PostmanRuntime/7.29.2"
    assert new_db_token.ip_address == "127.0.0.1"
