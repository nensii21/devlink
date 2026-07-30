from uuid import UUID

# pyrefly: ignore [missing-import]
import uuid
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import httpx
from app.core.config import settings
from app.core.security import (
    decode_token,
    is_refresh_token,
    create_verification_token,
)

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.middleware.rate_limit import (
    limiter,
    LOGIN_LIMIT,
    PASSWORD_RESET_LIMIT,
    REGISTER_LIMIT,
)
from app.dependencies import get_database
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    GitHubLoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    LogoutResponse,
    CurrentUserResponse,
    ChangePasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    SuccessResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ResendVerificationEmailRequest,
)
from app.schemas.user import CurrentUser
from app.services.auth_service import AuthService

router = APIRouter(
    tags=["Authentication"],
)

# ==========================================================
# Register
# ==========================================================


@router.post(
    "/register",
    response_model=CurrentUser,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit(REGISTER_LIMIT)
def register(
    request: Request,
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
@limiter.limit(LOGIN_LIMIT)
def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_database),
):
    """
    Authenticate a user.
    """

    auth_service = AuthService(db)
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    return auth_service.login(payload, user_agent=user_agent, ip_address=ip_address)


# ==========================================================
# Refresh Access Token
# ==========================================================


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh JWT",
)
@limiter.limit("10/minute")
def refresh(
    request: Request,
    payload: RefreshTokenRequest,
    db: Session = Depends(get_database),
):
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    auth_service = AuthService(db)

    return auth_service.refresh_token(
        payload.refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
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
# Logout
# ==========================================================


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout",
)
@limiter.limit("10/minute")
def logout(
    request: Request,
    payload: LogoutRequest | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):

    auth_service = AuthService(db)
    refresh_token_str = payload.refresh_token if payload else None

    return auth_service.logout(user_id, refresh_token_str=refresh_token_str)


import httpx  # noqa: E402
from app.schemas.auth import GitHubLoginRequest  # noqa: E402


@router.post(
    "/github",
    response_model=AuthResponse,
    summary="GitHub OAuth Login",
)
@limiter.limit(LOGIN_LIMIT)
async def github_login(
    request: Request,
    payload: GitHubLoginRequest,
    db: Session = Depends(get_database),
):
    """
    Authenticate a user via GitHub OAuth.
    """
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth is not configured.",
        )

    # 1. Exchange code for access token
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": payload.code,
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, json=data, headers=headers)
        if token_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange code for GitHub token.",
            )

        token_data = token_res.json()
        if "error" in token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=token_data.get("error_description", "Invalid GitHub code."),
            )

        access_token = token_data["access_token"]

        # 2. Fetch user profile
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch GitHub profile.",
            )
        github_user = user_res.json()

        # 3. Fetch user emails
        emails_res = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        primary_email = None
        if emails_res.status_code == 200:
            emails = emails_res.json()
            for email_obj in emails:
                if email_obj.get("primary") and email_obj.get("verified"):
                    primary_email = email_obj.get("email")
                    break

            if not primary_email:
                for email_obj in emails:
                    if email_obj.get("verified"):
                        primary_email = email_obj.get("email")
                        break

    if not primary_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A verified primary email is required for GitHub login.",
        )

    auth_service = AuthService(db)
    return auth_service.github_login(github_user, primary_email)


# ==========================================================
# Current User
# ==========================================================


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Current authenticated user",
)
@limiter.limit("30/minute")
def me(
    request: Request,
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
@limiter.limit("10/minute")
def refresh(
    request: Request,
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

    return auth_service.refresh_token(payload.refresh_token)


# ==========================================================
# Logout
# ==========================================================


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout",
)
@limiter.limit("10/minute")
def logout(
    request: Request,
    payload: LogoutRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):

    auth_service = AuthService(db)

    return auth_service.logout(user_id, payload.refresh_token)


# ==========================================================
# Logout From All Devices (bonus)
# ==========================================================


@router.post(
    "/logout-all",
    response_model=LogoutResponse,
    summary="Logout from all devices",
)
@limiter.limit("10/minute")
def logout_all(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):

    auth_service = AuthService(db)

    return auth_service.logout_all_devices(user_id)


# ==========================================================
# User Session Management (Issue #248)
# ==========================================================

from typing import List
from fastapi import Query
from app.models.user import User
from app.dependencies import get_current_user
from app.schemas.session import SessionResponse, RevokeSessionResponse
from app.services.refresh_token_service import RefreshTokenService


@router.get(
    "/sessions",
    response_model=List[SessionResponse],
    summary="List Active Sessions",
)
@limiter.limit("30/minute")
def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    current_session_id: uuid.UUID | None = Query(
        None, description="Optional ID of current session"
    ),
):
    """
    List all active sessions for the current user.
    """
    tokens = RefreshTokenService.get_active_sessions(db, current_user.id)
    results = []
    for token in tokens:
        item = SessionResponse.model_validate(token)
        if current_session_id and token.id == current_session_id:
            item.is_current = True
        results.append(item)
    return results


@router.delete(
    "/sessions/{session_id}",
    response_model=RevokeSessionResponse,
    summary="Revoke Individual Session",
)
@limiter.limit("20/minute")
def revoke_session(
    request: Request,
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """
    Revoke a specific active session by ID.
    """
    revoked = RefreshTokenService.revoke_session_by_id(db, session_id, current_user.id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already revoked.",
        )
    return RevokeSessionResponse(
        success=True,
        message="Session revoked successfully.",
        revoked_count=1,
    )


@router.post(
    "/sessions/revoke-others",
    response_model=RevokeSessionResponse,
    summary="Revoke All Other Sessions",
)
@limiter.limit("10/minute")
def revoke_other_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    current_session_id: uuid.UUID | None = Query(
        None, description="Current session ID to keep active"
    ),
):
    """
    Revoke all active sessions for current user except the current session.
    """
    count = RefreshTokenService.revoke_other_sessions(
        db=db,
        user_id=current_user.id,
        current_session_id=current_session_id,
    )
    return RevokeSessionResponse(
        success=True,
        message=f"Revoked {count} other session(s).",
        revoked_count=count,
    )


@router.delete(
    "/sessions",
    response_model=RevokeSessionResponse,
    summary="Revoke All Active Sessions",
)
@router.post(
    "/logout-all",
    response_model=RevokeSessionResponse,
    summary="Logout from all devices",
)
@limiter.limit("10/minute")
def logout_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """
    Revoke all active sessions for current user (logout from all devices).
    """
    RefreshTokenService.revoke_all_tokens(db, current_user.id)
    db.commit()
    return RevokeSessionResponse(
        success=True,
        message="All sessions revoked successfully.",
        revoked_count=1,
    )


# Forgot Password
# ==========================================================
from app.schemas.auth import (  # noqa: E402
    ChangePasswordRequest,
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
@limiter.limit("5/minute")
def change_password(
    request: Request,
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
@limiter.limit(PASSWORD_RESET_LIMIT)
def forgot_password(
    request: Request,
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
@limiter.limit(PASSWORD_RESET_LIMIT)
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_database),
):
    auth_service = AuthService(db)
    return auth_service.reset_password(
        token=payload.token,
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
@limiter.limit("5/minute")
def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    db: Session = Depends(get_database),
):

    try:
        token_payload = decode_token(payload.token)
        if token_payload.get("type") != "verification":
            raise ValueError("Invalid verification token type.")

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
@limiter.limit("3/hour")
def resend_verification(
    request: Request,
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
            "message": ("If the account exists, a verification email has been sent."),
        }

    # Generate verification token
    token = create_verification_token(str(user.id))  # noqa: F841
    create_verification_token(str(user.id))
    # TODO:
    # Send email via SMTP

    return {
        "success": True,
        "message": "Verification email sent.",
    }
