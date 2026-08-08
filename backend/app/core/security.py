from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
import bcrypt

# bcrypt refuses passwords longer than 72 bytes. passlib does not truncate for
# us, so the call is wrapped to do it.
#
# This block was duplicated -- the identical patch appeared twice, presumably
# from a bad merge -- and the second copy captured the *already patched*
# function as its `_original_hashpw`. `_patched_hashpw` therefore called
# itself, and every password hash died with:
#
#     RecursionError: maximum recursion depth exceeded
#
# which took registration and login with it. Nothing caught it because
# tests/conftest.py replaces pwd_context with a mock before the suite runs, so
# bcrypt is never exercised there.
#
# `_ALREADY_PATCHED` makes reapplying the patch a no-op, so a re-import or a
# future duplicate cannot recreate the loop.
if not getattr(bcrypt.hashpw, "_devlink_patched", False):
    _original_hashpw = bcrypt.hashpw

    def _patched_hashpw(password, salt):
        if len(password) > 72:
            return _original_hashpw(password[:72], salt)
        return _original_hashpw(password, salt)

    _patched_hashpw._devlink_patched = True
    bcrypt.hashpw = _patched_hashpw

from passlib.context import CryptContext  # noqa: E402

from app.core.config import settings  # noqa: E402

# ------------------------------------------------------------------
# Password Hashing
# ------------------------------------------------------------------

pwd_context = CryptContext(
    schemes=[settings.PASSWORD_HASH_SCHEME],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a plain text password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    """
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


# ------------------------------------------------------------------
# JWT Tokens
# ------------------------------------------------------------------


def _create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Internal JWT token creator.
    """

    now = datetime.now(timezone.utc)

    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }

    if extra:
        payload.update(extra)

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(
    user_id: str,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate JWT access token.
    """

    return _create_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
        extra=extra,
    )


import uuid


def create_refresh_token(
    user_id: str,
) -> str:
    """
    Generate refresh token.
    """

    return _create_token(
        subject=user_id,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
        extra={"jti": str(uuid.uuid4())},
    )


def create_verification_token(
    user_id: str,
) -> str:
    """
    Generate email verification token.
    """

    return _create_token(
        subject=user_id,
        expires_delta=timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
        token_type="verification",
    )


def is_verification_token(token: str) -> bool:
    """
    Check if token is an email verification token.
    """

    payload = decode_token(token)

    return payload.get("type") == "verification"


# ------------------------------------------------------------------
# Decode Tokens
# ------------------------------------------------------------------


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        return payload

    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


# ------------------------------------------------------------------
# Token Helpers
# ------------------------------------------------------------------


def get_user_id(token: str) -> Optional[str]:
    """
    Extract user ID from token.
    """

    payload = decode_token(token)

    return payload.get("sub")


def is_access_token(token: str) -> bool:
    """
    Check if token is an access token.
    """

    payload = decode_token(token)

    return payload.get("type") == "access"


def is_refresh_token(token: str) -> bool:
    """
    Check if token is a refresh token.
    """

    payload = decode_token(token)

    return payload.get("type") == "refresh"


# ------------------------------------------------------------------
# Password Strength
# ------------------------------------------------------------------


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password against minimum security rules.
    """

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if not any(c.isupper() for c in password):
        return False, "Password must contain an uppercase letter."

    if not any(c.islower() for c in password):
        return False, "Password must contain a lowercase letter."

    if not any(c.isdigit() for c in password):
        return False, "Password must contain a number."

    if not any(not c.isalnum() for c in password):
        return False, "Password must contain a special character."

    return True, "Password is strong."


# ------------------------------------------------------------------
# Security Utilities
# ------------------------------------------------------------------


def generate_token_payload(user_id: str, email: str) -> Dict[str, Any]:
    """
    Common payload included in JWTs.
    """

    return {
        "uid": user_id,
        "email": email,
    }
