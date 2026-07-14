from __future__ import annotations

# pyrefly: ignore [missing-import]
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(
    tags=["Authentication"],
)

# ==========================================================
# Register
# ==========================================================


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_database),
):
    """
    Create a new DevLink account.
    """

    auth_service = AuthService(db)

    user = auth_service.register(payload)

    return user


# ==========================================================
# Login
# ==========================================================


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login",
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_database),
):
    """
    Authenticate a user.
    """

    auth_service = AuthService(db)

    return auth_service.login(payload)


# pyrefly: ignore [missing-import]
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import (
    decode_token,
    is_refresh_token,
)
from app.schemas.auth import (
    RefreshTokenRequest,
    LogoutResponse,
    CurrentUserResponse,
)

security = HTTPBearer()


# ==========================================================
# Current Authenticated User Dependency
# ==========================================================


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Extract the current user's ID from the JWT.
    """

    try:
        payload = decode_token(credentials.credentials)

        return payload["sub"]

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        )


# ==========================================================
# Current User
# ==========================================================


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Current authenticated user",
)
def me(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):

    auth_service = AuthService(db)

    return auth_service.get_current_user(user_id)


# ==========================================================
# Refresh Access Token
# ==========================================================


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh JWT",
)
def refresh(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_database),
):

    try:
        token_payload = decode_token(payload.refresh_token)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    if not is_refresh_token(payload.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    auth_service = AuthService(db)

    return auth_service.refresh_token(token_payload["sub"])


# ==========================================================
# Logout
# ==========================================================


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout",
)
def logout(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):

    auth_service = AuthService(db)

    return auth_service.logout(user_id)


from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    SuccessResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ResendVerificationEmailRequest,
)

# ==========================================================
# Change Password
# ==========================================================


@router.patch(
    "/change-password",
    response_model=SuccessResponse,
    summary="Change Password",
)
def change_password(
    payload: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):

    auth_service = AuthService(db)

    return auth_service.change_password(
        user_id=user_id,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )


# ==========================================================
# Forgot Password
# ==========================================================


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Forgot Password",
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_database),
):

    auth_service = AuthService(db)

    return auth_service.forgot_password(
        payload.email,
    )


# ==========================================================
# Reset Password
# ==========================================================


@router.post(
    "/reset-password",
    response_model=SuccessResponse,
    summary="Reset Password",
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_database),
):
    """
    NOTE

    Currently this endpoint assumes the reset token
    contains the user's UUID.

    Later we'll replace this with secure signed reset
    tokens stored in Redis.
    """

    try:
        token_payload = decode_token(payload.token)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token.",
        )

    auth_service = AuthService(db)

    return auth_service.reset_password(
        user_id=token_payload["sub"],
        new_password=payload.new_password,
    )


# ==========================================================
# Verify Email
# ==========================================================


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    summary="Verify Email",
)
def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_database),
):

    try:
        token_payload = decode_token(payload.token)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification token.",
        )

    auth_service = AuthService(db)

    return auth_service.verify_email(
        token_payload["sub"],
    )


# ==========================================================
# Resend Verification Email
# ==========================================================


@router.post(
    "/resend-verification",
    response_model=SuccessResponse,
    summary="Resend Verification Email",
)
def resend_verification(
    payload: ResendVerificationEmailRequest,
    db: Session = Depends(get_database),
):
    """
    Placeholder.

    Email sending will be implemented after the
    SMTP service is added.
    """

    auth_service = AuthService(db)

    user = auth_service.get_user_by_email(
        payload.email,
    )

    if not user:
        return {
            "success": True,
            "message": (
                "If the account exists, " "a verification email has been sent."
            ),
        }

    # TODO:
    # Generate verification token
    # Send email via SMTP

    return {
        "success": True,
        "message": "Verification email sent.",
    }
