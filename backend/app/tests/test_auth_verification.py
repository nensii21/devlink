import pytest
from datetime import timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dependencies import get_database
from app.main import app
from app.models.user import User
from app.core.config import settings
from app.core.security import (
    create_verification_token,
    create_access_token,
    create_refresh_token,
    decode_token,
)

# Setup in-memory SQLite database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_database] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def create_unverified_user(db, email="test@example.com", username="testuser"):
    user = User(
        first_name="Test",
        last_name="User",
        username=username,
        email=email,
        password_hash="hashed_password",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_verify_email_success(client, db):
    user = create_unverified_user(db)
    
    # Generate a valid token
    token = create_verification_token(str(user.id))
    
    # Call verify-email endpoint
    response = client.post("/api/auth/verify-email", json={"token": token})
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
    assert response.json()["message"] == "Email verified successfully."
    
    # Check that user is marked verified in DB
    db.refresh(user)
    assert user.is_verified is True
    assert user.email_verified_at is not None


def test_verify_email_expired_token(client, db):
    user = create_unverified_user(db)
    
    # Temporarily set expiry to negative hours to force immediate expiration
    original_expiry = settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    try:
        settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = -1
        expired_token = create_verification_token(str(user.id))
    finally:
        settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = original_expiry
    
    # Verify rejection
    response = client.post("/api/auth/verify-email", json={"token": expired_token})
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid verification token."
    
    # Ensure user is still not verified
    db.refresh(user)
    assert user.is_verified is False


def test_verify_email_invalid_token_type(client, db):
    user = create_unverified_user(db)
    
    # Generate an access token instead of a verification token
    access_token = create_access_token(str(user.id))
    
    # Try verifying with it
    response = client.post("/api/auth/verify-email", json={"token": access_token})
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid verification token."
    
    # Try with a refresh token
    refresh_token = create_refresh_token(str(user.id))
    response = client.post("/api/auth/verify-email", json={"token": refresh_token})
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid verification token."
    
    # Ensure user is still not verified
    db.refresh(user)
    assert user.is_verified is False


def test_verify_email_malformed_token(client, db):
    user = create_unverified_user(db)
    
    response = client.post("/api/auth/verify-email", json={"token": "this.is.an.invalid.token"})
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid verification token."
    
    # Ensure user is still not verified
    db.refresh(user)
    assert user.is_verified is False


def test_verification_token_expiry_configurable():
    original_expiry = settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    try:
        settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = 5
        token = create_verification_token("test_user_id")
        
        payload = decode_token(token)
        # Calculate difference between exp and iat
        time_diff_seconds = payload["exp"] - payload["iat"]
        # Expected expiry: 5 hours (18000 seconds)
        assert time_diff_seconds == pytest.approx(18000, abs=5)
    finally:
        settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = original_expiry
