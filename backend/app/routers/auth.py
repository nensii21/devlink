# pyrefly: ignore [missing-import]
import uuid
import redis
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
    TokenType,
    create_verification_token,
    decode_access_token,
    decode_token,
)

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.middleware.rate_limit import (
    limiter,
    AUTH_LIMIT,
    LOGIN_LIMIT,
    REGISTER_LIMIT,
    PASSWORD_RESET_LIMIT,
    VERIFY_EMAIL_LIMIT,
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
from app.services.email_service import EmailService

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
@limiter.limit(AUTH_LIMIT)
def refresh(
    request: Request,
    payload: RefreshTokenRequest,
    db: Session = Depends(get_database),
):
    # Decoding with the expected type folds the signature, expiry and type
    # checks into one pass, and rejects a non-refresh token before we go
    # anywhere near the database.
    try:
        decode_token(payload.refresh_token, expected_type=TokenType.REFRESH)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

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
    Extract the current user's ID from the JWT access token.

    Only an access token is accepted. This dependency previously decoded
    without checking the ``type`` claim, so a refresh token -- or the token
    from a verification or password-reset email -- authenticated here,
    including on the endpoints below that change the password and revoke
    sessions.
    """

    try:
        payload = decode_access_token(credentials.credentials)

        return payload["sub"]

    except (ValueError, KeyError):
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
@limiter.limit(AUTH_LIMIT)
def logout(
    request: Request,
    payload: LogoutRequest | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):

    auth_service = AuthService(db)

    # The body is optional: a client that has already discarded its refresh
    # token can still log out, and the access token identifies the session.
    refresh_token_str = payload.refresh_token if payload else None

    return auth_service.logout(user_id, refresh_token_str=refresh_token_str)


oauth_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)


from app.schemas.auth import (
    LinkedInLoginRequest,
    OAuthStateResponse,
)  # noqa: E402

# ==========================================================
# GitHub OAuth Authorization (CSRF State)
# ==========================================================

# Redis client for OAuth state storage
oauth_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.get(
    "/github/authorize",
    response_model=OAuthStateResponse,
    summary="Get GitHub OAuth State",
)
async def github_authorize():
    """
    Generate a CSRF state parameter for GitHub OAuth flow.
    The state is stored in Redis with a 10-minute TTL.
    Frontend should include this state when redirecting to GitHub's authorize URL.
    """
    state = secrets.token_urlsafe(32)
    await oauth_redis.setex(f"oauth:state:{state}", 600, "1")
    return OAuthStateResponse(state=state)


import redis
import secrets
from app.schemas.auth import (
    OAuthStateResponse,
    MicrosoftLoginRequest,
    GoogleLoginRequest,
)  # noqa: E402
from app.core.config import settings


@router.post(
    "/github",
    response_model=AuthResponse,
    summary="GitHub OAuth Login",
)
@limiter.limit(AUTH_LIMIT)
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

    # Validate CSRF state
    state = payload.state
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth state parameter.",
        )

    state_key = f"oauth:state:{state}"
    state_valid = await oauth_redis.get(state_key)
    if not state_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state.",
        )
    await oauth_redis.delete(state_key)

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
# LinkedIn OAuth Authorization (CSRF State)
# ==========================================================


@router.get(
    "/linkedin/authorize",
    response_model=OAuthStateResponse,
    summary="Get LinkedIn OAuth State",
)
async def linkedin_authorize():
    state = secrets.token_urlsafe(32)
    await oauth_redis.setex(f"oauth:state:{state}", 600, "1")
    return OAuthStateResponse(state=state)


# ==========================================================
# LinkedIn OAuth Login
# ==========================================================


@router.post(
    "/linkedin",
    response_model=AuthResponse,
    summary="LinkedIn OAuth Login",
)
@limiter.limit(AUTH_LIMIT)
async def linkedin_login(
    request: Request,
    payload: LinkedInLoginRequest,
    db: Session = Depends(get_database),
):
    if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="LinkedIn OAuth is not configured.",
        )

    state = payload.state
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth state parameter.",
        )
    state_key = f"oauth:state:{state}"
    state_valid = await oauth_redis.get(state_key)
    if not state_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state.",
        )
    await oauth_redis.delete(state_key)

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        "code": payload.code,
        "grant_type": "authorization_code",
        "redirect_uri": "",
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data=data, headers=headers)
        if token_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange code for LinkedIn token.",
            )
        token_data = token_res.json()
        if "error" in token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=token_data.get("error_description", "Invalid LinkedIn code."),
            )

        access_token = token_data["access_token"]

        user_res = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch LinkedIn profile.",
            )
        linkedin_user = user_res.json()

        primary_email = linkedin_user.get("email")
        if not primary_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A verified email is required for LinkedIn login.",
            )

    auth_service = AuthService(db)
    return auth_service.linkedin_login(linkedin_user, primary_email)


# ==========================================================
# Current User
# ==========================================================


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Current authenticated user",
)
@limiter.limit(AUTH_LIMIT)
def me(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_database),
):

    auth_service = AuthService(db)

    return auth_service.get_current_user(user_id)


# `/refresh` and `/logout` were each declared a second time here, roughly 350
# lines below the originals. Both decorators ran at import, so both routes were
# registered on the router and Starlette served whichever it matched first --
# the earlier one. The copies below were therefore dead in every sense except
# the OpenAPI schema, where they showed up as duplicate operations.
#
# The behaviour worth keeping from them (the explicit refresh-token type check,
# and `AUTH_LIMIT` in place of a hardcoded "10/minute") has been folded into the
# live handlers above.


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
    VerifyRecoveryTokenResponse,
)

# ==========================================================
# Change Password
# ==========================================================


@router.patch(
    "/change-password",
    response_model=SuccessResponse,
    summary="Change Password",
)
@limiter.limit(AUTH_LIMIT)
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
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    auth_service = AuthService(db)

    return auth_service.forgot_password(
        email=payload.email,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.get(
    "/verify-recovery-token",
    response_model=VerifyRecoveryTokenResponse,
    summary="Verify Recovery Token Status",
    description="Validates a password recovery token without consuming it.",
)
@limiter.limit(PASSWORD_RESET_LIMIT)
def verify_recovery_token(
    request: Request,
    token: str = Query(..., description="Recovery token string"),
    db: Session = Depends(get_database),
):
    auth_service = AuthService(db)
    return auth_service.verify_recovery_token(token)


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
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    auth_service = AuthService(db)
    return auth_service.reset_password(
        token=payload.token,
        new_password=payload.new_password,
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ==========================================================
# Verify Email
# ==========================================================


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    summary="Verify Email",
)
@limiter.limit(VERIFY_EMAIL_LIMIT)
def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    db: Session = Depends(get_database),
):

    try:
        token_payload = decode_token(
            payload.token, expected_type=TokenType.VERIFICATION
        )

    except ValueError:
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
@limiter.limit(VERIFY_EMAIL_LIMIT)
def resend_verification(
    request: Request,
    payload: ResendVerificationEmailRequest,
    db: Session = Depends(get_database),
):

    auth_service = AuthService(db)

    user = auth_service.get_user_by_email(
        payload.email,
    )

    if not user:
        return {
            "success": True,
            "message": ("If the account exists, a verification email has been sent."),
        }

    if user.is_verified:
        return {
            "success": True,
            "message": "Your email is already verified.",
        }

    token = create_verification_token(str(user.id))
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    html = f"""
    <html>
        <body>
            <h2>Verify Your Email</h2>
            <p>Click the link below to verify your email address:</p>
            <p><a href="{verify_url}">Verify Email</a></p>
            <p>This link expires in 24 hours.</p>
            <br/>
            <p>Thanks,<br/>The DevLink Team</p>
        </body>
    </html>
    """
    EmailService.send_email(
        to_email=user.email,
        subject="Verify Your Email - DevLink",
        html_content=html,
    )

    return {
        "success": True,
        "message": "Verification email sent.",
    }


# ==========================================================
# Microsoft OAuth
# ==========================================================


@router.get(
    "/microsoft/authorize",
    response_model=OAuthStateResponse,
    summary="Get Microsoft OAuth State",
)
async def microsoft_authorize():
    """
    Generate a CSRF state parameter for Microsoft OAuth flow.
    The state is stored in Redis with a 10-minute TTL.
    Frontend should include this state when redirecting to Microsoft's authorize URL.
    """
    state = secrets.token_urlsafe(32)
    await oauth_redis.setex(f"oauth:state:{state}", 600, "1")
    return OAuthStateResponse(state=state)


@router.post(
    "/microsoft",
    response_model=AuthResponse,
    summary="Microsoft OAuth Login",
)
@limiter.limit(LOGIN_LIMIT)
async def microsoft_login(
    request: Request,
    payload: MicrosoftLoginRequest,
    db: Session = Depends(get_database),
):
    """
    Authenticate a user via Microsoft OAuth.
    """
    if not settings.MICROSOFT_CLIENT_ID or not settings.MICROSOFT_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft OAuth is not configured.",
        )

    # Validate CSRF state
    state = payload.state
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth state parameter.",
        )

    state_key = f"oauth:state:{state}"
    state_valid = await oauth_redis.get(state_key)
    if not state_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state.",
        )
    await oauth_redis.delete(state_key)

    # 1. Exchange code for access token
    tenant_id = settings.MICROSOFT_TENANT_ID or "common"
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "client_secret": settings.MICROSOFT_CLIENT_SECRET,
        "code": payload.code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data=data)
        if token_res.status_code != 200:
            token_error = token_res.json() if token_res.text else {}
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=token_error.get(
                    "error_description", "Failed to exchange code for Microsoft token."
                ),
            )

        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Microsoft token response did not contain an access token.",
            )

        # 2. Fetch user profile from Microsoft Graph API
        user_res = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch Microsoft profile.",
            )

        ms_user = user_res.json()

        primary_email = ms_user.get("mail") or ms_user.get("userPrincipalName")

        if not primary_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Microsoft profile does not have a primary email.",
            )

    # 3. Call AuthService to handle the login/linking
    auth_service = AuthService(db)
    return auth_service.microsoft_login(ms_user, primary_email)


# ==========================================================
# Google OAuth
# ==========================================================


@router.get(
    "/google/authorize",
    response_model=OAuthStateResponse,
    summary="Get Google OAuth State",
)
async def google_authorize():
    """
    Generate a CSRF state parameter for Google OAuth flow.
    The state is stored in Redis with a 10-minute TTL.
    """
    state = secrets.token_urlsafe(32)
    await oauth_redis.setex(f"oauth:state:{state}", 600, "1")
    return OAuthStateResponse(state=state)


@router.post(
    "/google",
    response_model=AuthResponse,
    summary="Google OAuth Login",
)
@limiter.limit(LOGIN_LIMIT)
async def google_login(
    request: Request,
    payload: GoogleLoginRequest,
    db: Session = Depends(get_database),
):
    """
    Authenticate a user via Google OAuth.
    """
    if (
        not settings.GOOGLE_CLIENT_ID
        or not settings.GOOGLE_CLIENT_SECRET
        or not settings.GOOGLE_REDIRECT_URI
    ):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured.",
        )

    # Validate CSRF state
    state = payload.state
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth state parameter.",
        )

    state_key = f"oauth:state:{state}"
    state_valid = await oauth_redis.get(state_key)
    if not state_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state.",
        )
    await oauth_redis.delete(state_key)

    # 1. Exchange code for access token
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": payload.code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data=data)
        if token_res.status_code != 200:
            token_error = token_res.json() if token_res.text else {}
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=token_error.get(
                    "error_description", "Failed to exchange code for Google token."
                ),
            )

        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token response did not contain an access token.",
            )

        # 2. Fetch user profile from Google API
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch Google profile.",
            )

        google_user = user_res.json()

        primary_email = google_user.get("email")

        if not primary_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google profile does not have an email.",
            )

    # 3. Call AuthService to handle the login/linking
    auth_service = AuthService(db)
    return auth_service.google_login(google_user, primary_email)
