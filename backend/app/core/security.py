from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

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
    )


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
