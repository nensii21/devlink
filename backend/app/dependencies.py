from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService

# ---------------------------------------------------------------------
# JWT Security Scheme
# ---------------------------------------------------------------------

security = HTTPBearer(auto_error=True)


# ---------------------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------------------

def get_database() -> Session:
    """
    Alias for get_db().
    """

    yield from get_db()


# ---------------------------------------------------------------------
# Current User
# ---------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database),
) -> User:
    """
    Returns the currently authenticated user.

    Raises:
        401 Unauthorized if token is invalid.
    """

    try:
        payload = decode_token(credentials.credentials)

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
            )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )

    auth_service = AuthService(db)

    user = auth_service.get_current_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


# ---------------------------------------------------------------------
# Active User
# ---------------------------------------------------------------------

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Returns only active users.
    """

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account.",
        )

    return current_user


# ---------------------------------------------------------------------
# Verified User
# ---------------------------------------------------------------------

def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Returns only verified users.
    """

    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required.",
        )

    return current_user


# ---------------------------------------------------------------------
# Admin User
# ---------------------------------------------------------------------

def get_current_admin(
    current_user: User = Depends(get_current_verified_user),
) -> User:
    """
    Returns only administrators.
    """

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return current_user