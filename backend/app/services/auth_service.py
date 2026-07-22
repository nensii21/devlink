from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

# pyrefly: ignore [missing-import]
from fastapi import HTTPException, status

# pyrefly: ignore [missing-import]
from sqlalchemy import select

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.core.events import event_bus
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
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.username == username))

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

        event_bus.publish(
            "USER_REGISTERED",
            email=user.email,
            user_id=str(user.id),
        )

        return user

    # =====================================================
    # Login
    # =====================================================

    def login(self, payload: LoginRequest):

        payload.email = validate_email(payload.email)

        user = self.get_user_by_email(payload.email)

        if not user:
            print("USER NOT FOUND:", payload.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not verify_password(
            payload.password,
            user.password_hash,
        ):
            print("PASSWORD MISMATCH:", payload.password, user.password_hash)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            print("USER INACTIVE")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )

        user.last_login = datetime.now(timezone.utc)
        user.last_active_at = datetime.now(timezone.utc)

        self.db.flush()

        access_token = create_access_token(
            str(user.id),
            {
                "username": user.username,
                "email": user.email,
            },
        )

        refresh_token = create_refresh_token(str(user.id))

        event_bus.publish(
            "USER_LOGIN",
            email=user.email,
            user_id=str(user.id),
        )
        return {
            "success": True,
            "message": "Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    def github_login(self, github_user: dict, primary_email: str):
        from app.models.user import User
        from app.core.security import (
            hash_password,
            create_access_token,
            create_refresh_token,
        )
        from fastapi import HTTPException, status
        import secrets
        import string
        from datetime import datetime, timezone

        github_id = str(github_user.get("id"))

        user = self.db.query(User).filter(User.github_id == github_id).first()

        if not user:
            user = self.db.query(User).filter(User.email == primary_email).first()
            if user:
                user.github_id = github_id
                if not user.github_url:
                    user.github_url = github_user.get("html_url")
                if not user.profile_image:
                    user.profile_image = github_user.get("avatar_url")
                self.db.commit()
                self.db.refresh(user)
            else:
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                random_password = "".join(secrets.choice(alphabet) for i in range(16))
                name_parts = (github_user.get("name") or "").split(" ")
                first_name = (
                    name_parts[0] if len(name_parts) > 0 and name_parts[0] else "GitHub"
                )
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "User"

                base_username = (github_user.get("login") or "github_user").lower()[:50]
                username = base_username
                counter = 1
                while self.get_user_by_username(username):
                    suffix = str(counter)
                    username = f"{base_username[: 50 - len(suffix)]}{suffix}"
                    counter += 1

                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    email=primary_email,
                    password_hash=hash_password(random_password),
                    github_id=github_id,
                    github_url=github_user.get("html_url"),
                    profile_image=github_user.get("avatar_url"),
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.now(timezone.utc),
                    email_verified_at=datetime.now(timezone.utc),
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)

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
        refresh_token = create_refresh_token(str(user.id))

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    # =====================================================
    # Get User by ID
    # =====================================================

    def get_user_by_id(self, user_id: str | UUID) -> Optional[User]:
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                pass
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

        refresh_token = create_refresh_token(str(user.id))

        event_bus.publish(
            "ACCESS_TOKEN_REFRESHED",
            email=user.email,
        )

        return {
            "success": True,
            "message": "Token refreshed successfully.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
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

        self.db.flush()
        event_bus.publish(
            "PASSWORD_CHANGED",
            email=user.email,
            user_id=str(user.id),
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
        user.email_verified_at = datetime.now(timezone.utc)

        self.db.flush()

        event_bus.publish(
            "EMAIL_VERIFIED",
            email=user.email,
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
        event_bus.publish(
            "USER_LOGOUT",
            email=user.email,
            user_id=str(user.id),
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
                "message": ("If the account exists, a reset email has been sent."),
            }

        # TODO:
        # Generate reset token
        # Send email

        event_bus.publish(
            "PASSWORD_RESET_REQUESTED",
            email=user.email,
        )

        return {
            "success": True,
            "message": ("Password reset email sent."),
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

        user.password_hash = hash_password(new_password)

        self.db.flush()

        event_bus.publish(
            "PASSWORD_RESET_COMPLETED",
            email=user.email,
        )

        return {
            "success": True,
            "message": ("Password has been reset."),
        }
