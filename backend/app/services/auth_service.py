from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.services.email_service import EmailService
from app.core.config import settings

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
    _create_token,
    decode_token,
)
from app.models.user import User
from app.models.password_history import PasswordHistory
from app.models.refresh_token import RefreshToken
from app.services.refresh_token_service import RefreshTokenService
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

    PASSWORD_HISTORY_LIMIT = 5

    """
    Authentication service for DevLink.
    """

    def __init__(self, db: Session):
        self.db = db

    def _save_password_history(self, user: User) -> None:
        history = PasswordHistory(
            user_id=user.id,
            password_hash=user.password_hash,
        )

        self.db.add(history)
        self.db.flush()

        histories = (
            self.db.execute(
                select(PasswordHistory)
                .where(PasswordHistory.user_id == user.id)
                .order_by(PasswordHistory.created_at.desc())
            )
            .scalars()
            .all()
        )

        for old_history in histories[self.PASSWORD_HISTORY_LIMIT :]:
            self.db.delete(old_history)

    def _is_password_reused(
        self,
        user: User,
        new_password: str,
    ) -> bool:
        if verify_password(new_password, user.password_hash):
            return True
        histories = (
            self.db.execute(
                select(PasswordHistory)
                .where(PasswordHistory.user_id == user.id)
                .order_by(PasswordHistory.created_at.desc())
                .limit(self.PASSWORD_HISTORY_LIMIT)
            )
            .scalars()
            .all()
        )

        for history in histories:
            if verify_password(new_password, history.password_hash):
                return True
        return False

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

    def login(
        self,
        payload: LoginRequest,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ):

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
        user.last_seen = datetime.now(timezone.utc)
        user.last_active_at = datetime.now(timezone.utc)

        self.db.flush()

        access_token = create_access_token(
            str(user.id),
            {
                "username": user.username,
            },
        )

        refresh_token = create_refresh_token(str(user.id))
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        RefreshTokenService.create_token_for_user(
            db=self.db,
            user_id=user.id,
            token_str=refresh_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.db.commit()

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

    # GitHub OAuth Login
    # =====================================================

    def github_login(self, github_user: dict, primary_email: str):
        github_id = str(github_user["id"])

        # 1. Check if user already exists by github_id

        user = self.db.scalar(select(User).where(User.github_id == github_id))

        if not user:
            # 2. Check if user exists by email

            user = self.get_user_by_email(primary_email)
            if user:
                # Link account

                user.github_id = github_id
                user.github_url = github_user.get("html_url")
                if not user.profile_image and github_user.get("avatar_url"):
                    user.profile_image = github_user.get("avatar_url")
                self.db.commit()
            else:
                # 3. Create new user

                import secrets
                import string

                # Generate random password (local requirement)

                alphabet = string.ascii_letters + string.digits + string.punctuation
                random_password = "".join(secrets.choice(alphabet) for i in range(32))

                # Parse name

                name = (
                    github_user.get("name") or github_user.get("login") or "GitHub User"
                )
                name_parts = name.split(" ", 1)
                first_name = name_parts[0][:100]
                last_name = name_parts[1][:100] if len(name_parts) > 1 else ""

                # Ensure unique username

                base_username = (github_user.get("login") or "github_user").lower()[:50]
                username = base_username
                counter = 1
                while self.get_user_by_username(username):
                    suffix = str(counter)
                    username = f"{base_username[:50 - len(suffix)]}{suffix}"
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
                    is_verified=True,  # GitHub verified emails are trusted
                    created_at=datetime.now(timezone.utc),
                    email_verified_at=datetime.now(timezone.utc),
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
                event_bus.publish(
                    "USER_REGISTERED",
                    email=user.email,
                    user_id=str(user.id),
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

        refresh_token = create_refresh_token(str(user.id))
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        RefreshTokenService.create_token_for_user(
            db=self.db,
            user_id=user.id,
            token_str=refresh_token,
            expires_at=expires_at,
        )
        self.db.commit()

        event_bus.publish(
            "USER_LOGIN",
            email=user.email,
            user_id=str(user.id),
        )

        return {
            "success": True,
            "message": "GitHub login successful.",
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
        now = datetime.now(timezone.utc)
        last_seen = user.last_seen
        if last_seen and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        if not last_seen or (now - last_seen).total_seconds() > 60:
            user.last_seen = now
            self.db.commit()
        return user

    # =====================================================
    # Refresh Token
    # =====================================================

    def refresh_token(
        self,
        token_str: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ):
        db_token = RefreshTokenService.get_token(self.db, token_str)
        now = datetime.now(timezone.utc)

        if db_token and db_token.is_revoked:
            # Token reuse detected! Revoke all tokens for this user for security.

            RefreshTokenService.revoke_all_tokens(self.db, db_token.user_id)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has already been revoked or reused. All sessions revoked for security.",
            )
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )
        expires_at = db_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )
        user = self.get_current_user(str(db_token.user_id))

        # Rotate refresh token

        db_token.is_revoked = True
        db_token.revoked_at = now
        db_token.last_used_at = now

        new_access_token = create_access_token(
            str(user.id),
            {
                "username": user.username,
                "email": user.email,
            },
        )
        new_refresh_token = create_refresh_token(str(user.id))
        new_expires_at = now + timedelta(days=7)

        RefreshTokenService.create_token_for_user(
            db=self.db,
            user_id=user.id,
            token_str=new_refresh_token,
            expires_at=new_expires_at,
            user_agent=user_agent or db_token.user_agent,
            ip_address=ip_address or db_token.ip_address,
            device_name=db_token.device_name,
            device_type=db_token.device_type,
            browser=db_token.browser,
            operating_system=db_token.operating_system,
        )
        self.db.commit()

        event_bus.publish(
            "ACCESS_TOKEN_REFRESHED",
            email=user.email,
        )

        return {
            "success": True,
            "message": "Token refreshed successfully.",
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
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

        if self._is_password_reused(user, new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot reuse one of your last 5 passwords.",
            )
        self._save_password_history(user)

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

    def logout(self, user_id: str, refresh_token_str: str | None = None):

        user = self.get_current_user(user_id)
        if refresh_token_str:
            db_token = RefreshTokenService.get_token(self.db, refresh_token_str)
            if db_token and str(db_token.user_id) == str(user.id):
                RefreshTokenService.revoke_token(self.db, db_token)
                self.db.commit()
        event_bus.publish(
            "USER_LOGOUT",
            email=user.email,
            user_id=str(user.id),
        )
        return {
            "success": True,
            "message": "Logged out successfully.",
        }

    def logout_all_devices(self, user_id: str):
        """
        Revoke every refresh token belonging to this user
        (logs the user out everywhere).
        """

        user = self.get_current_user(user_id)

        RefreshTokenService.revoke_all_tokens(self.db, user.id)

        event_bus.publish(
            "USER_LOGOUT",
            email=user.email,
            user_id=str(user.id),
        )

        return {
            "success": True,
            "message": "Logged out from all devices.",
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
        pwd_hash_frag = user.password_hash[-10:] if user.password_hash else "nohash"

        token = _create_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=15),
            token_type="reset_password",
            extra={"hash_frag": pwd_hash_frag},
        )

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        EmailService.send_notification_email(
            to_email=user.email,
            title="Reset Your Password",
            message="You requested a password reset. This link will expire in 15 minutes.",
            action_url=reset_url,
        )

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
        token: str,
        new_password: str,
    ):
        try:
            payload = decode_token(token)
            if payload.get("type") not in ("reset", "reset_password"):
                raise ValueError("Invalid token type")
            user_id = payload.get("sub")
            hash_frag = payload.get("hash_frag")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )
        validate_password(new_password)

        user = self.get_current_user(user_id)

        expected_frag = user.password_hash[-10:] if user.password_hash else "nohash"
        if hash_frag and hash_frag != expected_frag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset token has already been used.",
            )
        if self._is_password_reused(user, new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot reuse one of your last 5 passwords.",
            )
        self._save_password_history(user)

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
