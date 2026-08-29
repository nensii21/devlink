from datetime import datetime, timezone, timedelta
import pytest
from fastapi import status
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.services.refresh_token_service import RefreshTokenService


def create_test_user(db, email="logout_test@example.com", username="logoutuser"):
    user = User(
        first_name="Logout",
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


def test_logout_success(client, db):
    user = create_test_user(db)
    refresh_token_str = create_refresh_token(str(user.id))
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Register token in DB
    db_token = RefreshTokenService.create_token_for_user(
        db=db,
        user_id=user.id,
        token_str=refresh_token_str,
        expires_at=expires_at,
    )
    db.commit()

    # Authenticate client
    access_token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {access_token}"}

    # Logout
    response = client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token_str},
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True

    # Assert revoked in DB
    db.refresh(db_token)
    assert db_token.is_revoked is True
    assert db_token.revoked_at is not None


def test_revoked_token_cannot_be_reused_to_refresh(client, db):
    user = create_test_user(db)
    refresh_token_str = create_refresh_token(str(user.id))
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Register token in DB and mark it as revoked
    db_token = RefreshTokenService.create_token_for_user(
        db=db,
        user_id=user.id,
        token_str=refresh_token_str,
        expires_at=expires_at,
    )
    db_token.is_revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    db.commit()

    # Attempt to refresh session with revoked token
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token_str},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "revoked" in response.json()["detail"].lower()


def test_refresh_token_reuse_revokes_all_sessions(client, db):
    user = create_test_user(db)

    # Create two refresh tokens
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
    db_token_1.is_revoked = True
    db_token_1.revoked_at = datetime.now(timezone.utc)
    db.commit()

    # Attempting to refresh with the already revoked token_1 should trigger security sweep
    # and revoke token_2 as well
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": token_1_str},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify both tokens are revoked
    db.refresh(db_token_1)
    db.refresh(db_token_2)
    assert db_token_1.is_revoked is True
    assert db_token_2.is_revoked is True
