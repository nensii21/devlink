from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import log_security_event
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
)
from app.utils.validators import (
    validate_email,
    validate_name,
    validate_password,
    validate_username,
)


class AuthService:
    """
    Authentication service for DevLink.
    """

    def __init__(self, db: Session):
        self.db = db

    # =====================================================
    # User Lookup Helpers
    # =====================================================

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.scalar(
            select(User).where(User.email == email.lower())
        )

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.scalar(
            select(User).where(User.username == username)
        )

    # =====================================================
    # Register
    # =====================================================

    def register(self, payload: RegisterRequest) -> User:

        payload.email = validate_email(payload.email)

        payload.first_name = validate_name(payload.first_name)

        payload.last_name = validate_name(payload.last_name)

        payload.username = validate_username(payload.username)

        validate_password(payload.password)

        if self.get_user_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists.",
            )

        if self.get_user_by_username(payload.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists.",
            )

        user = User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
            is_active=True,
            is_verified=False,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        log_security_event(
            event="New user registration",
            user=user.email,
        )

        return user

    # =====================================================
    # Login
    # =====================================================

    def login(self, payload: LoginRequest):

        payload.email = validate_email(payload.email)

        user = self.get_user_by_email(payload.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not verify_password(
            payload.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )

        user.last_login = datetime.now(timezone.utc)

        self.db.commit()

        access_token = create_access_token(
            str(user.id),
            {
                "username": user.username,
                "email": user.email,
            },
        )

        refresh_token = create_refresh_token(
            str(user.id)
        )

        log_security_event(
            event="Successful login",
            user=user.email,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }
        
            # =====================================================
    # Get User by ID
    # =====================================================

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.get(User, user_id)

    # =====================================================
    # Current User
    # =====================================================

    def get_current_user(self, user_id: str) -> User:

        user = self.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )

        return user

    # =====================================================
    # Refresh Token
    # =====================================================

    def refresh_token(self, user_id: str):

        user = self.get_current_user(user_id)

        access_token = create_access_token(
            str(user.id),
            {
                "username": user.username,
                "email": user.email,
            },
        )

        refresh_token = create_refresh_token(
            str(user.id)
        )

        log_security_event(
            event="Access token refreshed",
            user=user.email,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    # =====================================================
    # Change Password
    # =====================================================

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ):

        user = self.get_current_user(user_id)

        if not verify_password(
            current_password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect.",
            )

        validate_password(new_password)

        user.password_hash = hash_password(new_password)

        self.db.commit()

        log_security_event(
            event="Password changed",
            user=user.email,
        )

        return {
            "success": True,
            "message": "Password updated successfully.",
        }

    # =====================================================
    # Verify Email
    # =====================================================

    def verify_email(self, user_id: str):

        user = self.get_current_user(user_id)

        if user.is_verified:
            return {
                "success": True,
                "message": "Email already verified.",
            }

        user.is_verified = True
        user.email_verified_at = datetime.now(
            timezone.utc
        )

        self.db.commit()

        log_security_event(
            event="Email verified",
            user=user.email,
        )

        return {
            "success": True,
            "message": "Email verified successfully.",
        }

    # =====================================================
    # Logout
    # =====================================================

    def logout(self, user_id: str):

        user = self.get_current_user(user_id)

        log_security_event(
            event="Logout",
            user=user.email,
        )

        return {
            "success": True,
            "message": "Logged out successfully.",
        }

    # =====================================================
    # Forgot Password
    # =====================================================

    def forgot_password(self, email: str):

        user = self.get_user_by_email(email)

        if not user:
            return {
                "success": True,
                "message": (
                    "If the account exists, a reset email "
                    "has been sent."
                ),
            }

        # TODO:
        # Generate reset token
        # Send email

        log_security_event(
            event="Password reset requested",
            user=user.email,
        )

        return {
            "success": True,
            "message": (
                "Password reset email sent."
            ),
        }

    # =====================================================
    # Reset Password
    # =====================================================

    def reset_password(
        self,
        user_id: str,
        new_password: str,
    ):

        validate_password(new_password)

        user = self.get_current_user(user_id)

        user.password_hash = hash_password(
            new_password
        )

        self.db.commit()

        log_security_event(
            event="Password reset completed",
            user=user.email,
        )

        return {
            "success": True,
            "message": (
                "Password has been reset."
            ),
        }