import hashlib
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi import status
from sqlalchemy import select

from app.core.config import settings
from app.core.security import (
    TokenType,
    _create_token,
    decode_token,
    hash_password,
)
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken


def create_test_user(db, email="reset_test@example.com", username="resetuser"):
    user = User(
        first_name="Reset",
        last_name="User",
        username=username,
        email=email,
        password_hash=hash_password("oldpassword123"),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_forgot_password_success(client, db):
    user = create_test_user(db)

    # Call forgot password endpoint
    response = client.post("/api/auth/forgot-password", json={"email": user.email})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True

    # Check token was stored in DB
    token_record = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    )
    assert token_record is not None
    assert token_record.is_used is False
    assert token_record.expires_at > datetime.now(timezone.utc)


def test_verify_recovery_token_success(client, db):
    user = create_test_user(db)
    jti = str(uuid.uuid4())
    pwd_hash_frag = user.password_hash[-10:] if user.password_hash else "nohash"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    token = _create_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=15),
        token_type="reset_password",
        extra={"jti": jti, "hash_frag": pwd_hash_frag},
    )

    # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    token_record = PasswordResetToken(
        id=uuid.uuid4(),
        user_id=user.id,
        jti=jti,
        token_hash=token_hash,
        expires_at=expires_at,
        is_used=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(token_record)
    db.commit()

    # Verify recovery token check
    response = client.get(f"/api/auth/verify-recovery-token?token={token}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["valid"] is True
    assert response.json()["email"] == user.email


def test_reset_password_success(client, db):
    user = create_test_user(db)
    jti = str(uuid.uuid4())
    pwd_hash_frag = user.password_hash[-10:] if user.password_hash else "nohash"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    token = _create_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=15),
        token_type="reset_password",
        extra={"jti": jti, "hash_frag": pwd_hash_frag},
    )

    # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    token_record = PasswordResetToken(
        id=uuid.uuid4(),
        user_id=user.id,
        jti=jti,
        token_hash=token_hash,
        expires_at=expires_at,
        is_used=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(token_record)
    db.commit()

    # Perform password reset
    response = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "NewSecretPassword123!"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True

    # Assert token has been marked used in DB
    db.refresh(token_record)
    assert token_record.is_used is True
    assert token_record.used_at is not None

    # Verify that new password can be used for authentication / is hashed correctly
    db.refresh(user)
    assert user.password_hash != hash_password("oldpassword123")


def test_reset_password_expired(client, db):
    user = create_test_user(db)
    jti = str(uuid.uuid4())
    pwd_hash_frag = user.password_hash[-10:] if user.password_hash else "nohash"

    # Create token already expired in the past
    expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    token = _create_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=-5),  # negative delta causes expired claim
        token_type="reset_password",
        extra={"jti": jti, "hash_frag": pwd_hash_frag},
    )

    # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    token_record = PasswordResetToken(
        id=uuid.uuid4(),
        user_id=user.id,
        jti=jti,
        token_hash=token_hash,
        expires_at=expires_at,
        is_used=False,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    db.add(token_record)
    db.commit()

    # Verification of expired token should fail
    response = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "NewSecretPassword123!"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "expired" in response.json()["detail"].lower()


def test_reset_password_already_used(client, db):
    user = create_test_user(db)
    jti = str(uuid.uuid4())
    pwd_hash_frag = user.password_hash[-10:] if user.password_hash else "nohash"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    token = _create_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=15),
        token_type="reset_password",
        extra={"jti": jti, "hash_frag": pwd_hash_frag},
    )

    # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    token_record = PasswordResetToken(
        id=uuid.uuid4(),
        user_id=user.id,
        jti=jti,
        token_hash=token_hash,
        expires_at=expires_at,
        is_used=True,  # Mark as already used
        used_at=datetime.now(timezone.utc) - timedelta(minutes=2),
        created_at=datetime.now(timezone.utc),
    )
    db.add(token_record)
    db.commit()

    # Reset attempt with reused token should fail
    response = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "NewSecretPassword123!"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already been used" in response.json()["detail"].lower()


def test_reset_password_reused_password(client, db):
    user = create_test_user(db)
    jti = str(uuid.uuid4())
    pwd_hash_frag = user.password_hash[-10:] if user.password_hash else "nohash"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    token = _create_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=15),
        token_type="reset_password",
        extra={"jti": jti, "hash_frag": pwd_hash_frag},
    )

    # codeql[py/weak-sensitive-data-hashing] These are high entropy tokens, not passwords
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    token_record = PasswordResetToken(
        id=uuid.uuid4(),
        user_id=user.id,
        jti=jti,
        token_hash=token_hash,
        expires_at=expires_at,
        is_used=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(token_record)
    db.commit()

    # Reset with same password as current password should trigger reuse error (within last 5)
    response = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "oldpassword123"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot reuse" in response.json()["detail"].lower()
