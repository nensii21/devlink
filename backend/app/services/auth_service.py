from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from uuid import UUID

from app.services.email_service import EmailService
from app.services.suspicious_login_service import SuspiciousLoginService
from app.services.audit_log_service import AuditLogService
from app.models.audit_log import AuditAction
from app.core.config import settings

logger = logging.getLogger(__name__)

# pyrefly: ignore [missing-import]

from fastapi import HTTPException, status

# pyrefly: ignore [missing-import]

from sqlalchemy import select

# pyrefly: ignore [missing-import]

from sqlalchemy.orm import Session

from app.core.events import event_bus
from app.core.security import (
    InvalidTokenType,
    TokenType,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    _create_token,
    decode_token,
)
from app.models.user import User
from app.models.password_history import PasswordHistory
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

        validate_password(
            payload.password,
            username=payload.username,
            email=payload.email,
        )

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
            logger.warning("Login failed: user not found for email")
            # Log failed login and check suspicious signals
            AuditLogService.create_log(
                db=self.db,
                actor_id=None,
                action=AuditAction.FAILED_LOGIN,
                entity_type="user_session",
                entity_id=payload.email,
                description=f"Failed login attempt for email {payload.email}",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata_info={"email": payload.email},
                success=False,
            )
            self.db.commit()
            SuspiciousLoginService.evaluate_login_attempt(
                db=self.db,
                email=payload.email,
                ip_address=ip_address,
                user_agent=user_agent,
                user=None,
                is_success=False,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        if not verify_password(
            payload.password,
            user.password_hash,
        ):
            logger.warning("Login failed: password mismatch for user %s", user.id)
            # Log failed login and check suspicious signals
            AuditLogService.create_log(
                db=self.db,
                actor_id=user.id,
                action=AuditAction.FAILED_LOGIN,
                entity_type="user_session",
                entity_id=str(user.id),
                target_user_id=user.id,
                description=f"Failed password authentication for {payload.email}",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata_info={"email": payload.email},
                success=False,
            )
            self.db.commit()
            SuspiciousLoginService.evaluate_login_attempt(
                db=self.db,
                email=payload.email,
                ip_address=ip_address,
                user_agent=user_agent,
                user=user,
                is_success=False,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        if not user.is_active:
            logger.warning("Login blocked: inactive account %s", user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )

        # Check suspicious login signals for successful login
        suspicious_result = SuspiciousLoginService.evaluate_login_attempt(
            db=self.db,
            email=payload.email,
            ip_address=ip_address,
            user_agent=user_agent,
            user=user,
            is_success=True,
        )

        user.last_login = datetime.now(timezone.utc)
        user.last_seen = datetime.now(timezone.utc)
        user.last_active_at = datetime.now(timezone.utc)

        # Record successful login audit log
        AuditLogService.create_log(
            db=self.db,
            actor_id=user.id,
            action=AuditAction.LOGIN,
            entity_type="user_session",
            entity_id=str(user.id),
            target_user_id=user.id,
            description=f"User logged in from {ip_address or 'Unknown IP'}",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_info={
                "email": payload.email,
                "is_suspicious": suspicious_result.is_suspicious,
                "signals": suspicious_result.signals,
            },
            success=True,
        )

        self.db.flush()

        if user.mfa_enabled:
            # Not an access token: this only gets the caller as far as
            # `/api/auth/mfa/verify`. It used to be minted by
            # `create_access_token` with `extra={"type": "mfa_pending"}`,
            # relying on `extra` overwriting the type the creator had just
            # set -- which now raises. Same lifetime, stated outright.
            mfa_token = _create_token(
                subject=str(user.id),
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                token_type=TokenType.MFA_PENDING,
            )
            self.db.commit()
            return {
                "success": True,
                "mfa_required": True,
                "mfa_token": mfa_token,
                "message": "MFA verification required.",
            }

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

    def complete_mfa_login(
        self,
        mfa_token: str,
        code: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        try:
            payload = decode_token(mfa_token, expected_type=TokenType.MFA_PENDING)
            user_id = UUID(payload.get("sub"))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired MFA session token.",
            )

        user = self.db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account unavailable.",
            )

        from app.services.mfa_service import MFAService

        verified = MFAService.verify_user_mfa(self.db, user, code)
        if not verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code or recovery code.",
            )

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

        return {
            "success": True,
            "message": "MFA authentication successful.",
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
    # Microsoft OAuth
    # =====================================================

    def microsoft_login(self, microsoft_user: dict, primary_email: str):
        microsoft_id = str(microsoft_user["id"])

        # 1. Check if user already exists by microsoft_id
        user = self.db.scalar(select(User).where(User.microsoft_id == microsoft_id))

        if not user:
            # 2. Check if user exists by primary email
            user = self.db.scalar(select(User).where(User.email == primary_email))

            if user:
                # User exists by email, link Microsoft account safely
                if user.microsoft_id and user.microsoft_id != microsoft_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email is linked to another Microsoft account.",
                    )

                user.microsoft_id = microsoft_id

                # Assume verified since it came from MS
                if not user.is_verified:
                    user.is_verified = True
                    user.email_verified_at = datetime.now(timezone.utc)
            else:
                # 3. Create new user
                name_parts = (
                    microsoft_user.get("displayName")
                    or microsoft_user.get("givenName")
                    or "Microsoft User"
                ).split(" ")

                first_name = (
                    name_parts[0]
                    if len(name_parts) > 0 and name_parts[0]
                    else "Microsoft"
                )
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "User"

                base_username = (
                    (microsoft_user.get("userPrincipalName") or primary_email)
                    .split("@")[0]
                    .lower()[:50]
                )
                username = base_username
                counter = 1
                while self.db.scalar(select(User).where(User.username == username)):
                    username = f"{base_username}{counter}"
                    counter += 1

                import secrets

                random_password = secrets.token_urlsafe(32)

                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    email=primary_email,
                    password_hash=hash_password(random_password),
                    microsoft_id=microsoft_id,
                    is_active=True,
                    is_verified=True,
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
            "message": "Microsoft login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    # =====================================================
    # Google OAuth
    # =====================================================

    def google_login(self, google_user: dict, primary_email: str):
        google_id = str(google_user["id"])

        # 1. Check if user already exists by google_id
        user = self.db.scalar(select(User).where(User.google_id == google_id))

        if not user:
            # 2. Check if user exists by primary email
            user = self.db.scalar(select(User).where(User.email == primary_email))

            if user:
                # User exists by email, link Google account safely
                if user.google_id and user.google_id != google_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email is linked to another Google account.",
                    )

                user.google_id = google_id

                # Assume verified since it came from Google
                if not user.is_verified:
                    user.is_verified = True
                    user.email_verified_at = datetime.now(timezone.utc)
            else:
                # 3. Create new user
                first_name = google_user.get("given_name") or "Google"
                last_name = google_user.get("family_name") or "User"

                base_username = primary_email.split("@")[0].lower()[:50]
                username = base_username
                counter = 1
                while self.db.scalar(select(User).where(User.username == username)):
                    username = f"{base_username}{counter}"
                    counter += 1

                import secrets

                random_password = secrets.token_urlsafe(32)

                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    email=primary_email,
                    password_hash=hash_password(random_password),
                    google_id=google_id,
                    profile_image=google_user.get("picture"),
                    is_active=True,
                    is_verified=True,
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
            "message": "Google login successful.",
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
        validate_password(
            new_password,
            username=user.username,
            email=user.email,
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
    # =====================================================
    # Forgot Password & Account Recovery (#587)
    # =====================================================

    def forgot_password(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        import hashlib
        from app.models.password_reset_token import PasswordResetToken

        user = self.get_user_by_email(email)

        # Generic response to prevent account enumeration
        generic_msg = "If an account associated with this email exists, a password reset link has been sent."

        if not user:
            return {"success": True, "message": generic_msg}

        jti = str(uuid.uuid4())
        pwd_hash_frag = user.password_hash[-10:] if user.password_hash else "nohash"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        token = _create_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=15),
            token_type="reset_password",
            extra={"jti": jti, "hash_frag": pwd_hash_frag},
        )

        # lgtm[py/weak-sensitive-data-hashing]
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        # Store single-use recovery token record
        token_record = PasswordResetToken(
            id=uuid.uuid4(),
            user_id=user.id,
            jti=jti,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(token_record)
        self.db.flush()

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        EmailService.send_notification_email(
            to_email=user.email,
            title="Reset Your Password",
            message="You requested a password reset for your DevLink account. This link will expire in 15 minutes.",
            action_url=reset_url,
        )

        AuditLogService.create_log(
            db=self.db,
            actor_id=user.id,
            action=AuditAction.PASSWORD_RESET_REQUESTED,
            entity_type="user",
            entity_id=str(user.id),
            description=f"Password recovery requested for {user.email}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()

        event_bus.publish(
            "PASSWORD_RESET_REQUESTED",
            email=user.email,
        )

        return {"success": True, "message": generic_msg}

    def verify_recovery_token(self, token: str) -> dict:
        from app.models.password_reset_token import PasswordResetToken

        try:
            payload = decode_token(token, expected_type=TokenType.RESET_PASSWORD)
            user_id = payload.get("sub")
            jti = payload.get("jti")
            hash_frag = payload.get("hash_frag")
        except InvalidTokenType:
            return {"valid": False, "message": "Invalid token type."}
        except ValueError:
            return {"valid": False, "message": "Invalid or expired recovery token."}

        user = self.db.get(User, UUID(user_id)) if user_id else None
        if not user:
            return {
                "valid": False,
                "message": "User account associated with token not found.",
            }

        if jti:
            t_rec = self.db.scalar(
                select(PasswordResetToken).where(PasswordResetToken.jti == jti)
            )
            if t_rec:
                if t_rec.is_used:
                    return {
                        "valid": False,
                        "message": "This recovery token has already been used.",
                    }
                if t_rec.expires_at and t_rec.expires_at < datetime.now(timezone.utc):
                    return {
                        "valid": False,
                        "message": "This recovery token has expired.",
                    }

        expected_frag = user.password_hash[-10:] if user.password_hash else "nohash"
        if hash_frag and hash_frag != expected_frag:
            return {
                "valid": False,
                "message": "This recovery token has already been used.",
            }

        return {
            "valid": True,
            "message": "Recovery token is valid.",
            "email": user.email,
        }

    # =====================================================
    # Reset Password
    # =====================================================

    def reset_password(
        self,
        token: str,
        new_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        from app.models.password_reset_token import PasswordResetToken

        try:
            payload = decode_token(token, expected_type=TokenType.RESET_PASSWORD)
            user_id = payload.get("sub")
            jti = payload.get("jti")
            hash_frag = payload.get("hash_frag")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )

        user = self.get_current_user(user_id)

        token_record = None
        if jti:
            token_record = self.db.scalar(
                select(PasswordResetToken).where(PasswordResetToken.jti == jti)
            )
            if token_record:
                if token_record.is_used:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This reset token has already been used.",
                    )
                if token_record.expires_at and token_record.expires_at < datetime.now(
                    timezone.utc
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This reset token has expired.",
                    )

        expected_frag = user.password_hash[-10:] if user.password_hash else "nohash"
        if hash_frag and hash_frag != expected_frag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset token has already been used.",
            )

        validate_password(
            new_password,
            username=user.username,
            email=user.email,
        )

        if self._is_password_reused(user, new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot reuse one of your last 5 passwords.",
            )

        self._save_password_history(user)

        user.password_hash = hash_password(new_password)
        self.db.add(user)

        if token_record:
            token_record.is_used = True
            token_record.used_at = datetime.now(timezone.utc)
            self.db.add(token_record)

        RefreshTokenService.revoke_all_tokens(self.db, user.id)

        AuditLogService.create_log(
            db=self.db,
            actor_id=user.id,
            action=AuditAction.PASSWORD_RESET_COMPLETED,
            entity_type="user",
            entity_id=str(user.id),
            description=f"Account password successfully reset for {user.email}",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()

        event_bus.publish(
            "PASSWORD_RESET_COMPLETED",
            email=user.email,
        )

        return {
            "success": True,
            "message": "Password has been successfully reset. You can now log in with your new password.",
        }

    # =====================================================
    # LinkedIn OAuth Login
    # =====================================================

    def linkedin_login(self, linkedin_user: dict, primary_email: str):
        linkedin_id = str(linkedin_user["sub"])

        user = self.db.scalar(select(User).where(User.linkedin_id == linkedin_id))

        if not user:
            user = self.db.scalar(select(User).where(User.email == primary_email))
            if user:
                user.linkedin_id = linkedin_id
                if linkedin_user.get("picture"):
                    user.profile_image = linkedin_user["picture"]
                self.db.commit()
            else:
                import secrets
                import string

                alphabet = string.ascii_letters + string.digits + string.punctuation
                random_password = "".join(secrets.choice(alphabet) for i in range(32))

                name = linkedin_user.get("name") or "LinkedIn User"
                name_parts = name.split(" ", 1)
                first_name = name_parts[0][:100]
                last_name = name_parts[1][:100] if len(name_parts) > 1 else ""

                linkedin_username = (
                    linkedin_user.get("preferred_username") or "linkedin_user"
                ).lower()[:50]
                base_username = linkedin_username
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
                    linkedin_id=linkedin_id,
                    profile_image=linkedin_user.get("picture"),
                    is_active=True,
                    is_verified=True,
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
            "message": "LinkedIn login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }
