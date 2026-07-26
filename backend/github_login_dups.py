@router.post(
    "/github",
    response_model=AuthResponse,
    summary="GitHub OAuth Login",
)
async def github_login(
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


import httpx  # noqa: E402
from app.schemas.auth import GitHubLoginRequest  # noqa: E402
from app.core.config import settings  # noqa: E402


@router.post(
    "/github",
    response_model=AuthResponse,
    summary="GitHub OAuth Login",
)
async def github_login(
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


# pyrefly: ignore [missing-import]
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # noqa: E402

from app.core.security import (  # noqa: E402
    decode_token,
    is_refresh_token,
    create_verification_token,
)
from app.schemas.auth import (  # noqa: E402
    RefreshTokenRequest,
    LogoutResponse,
    CurrentUserResponse,
)


@router.post(
    "/github",
    response_model=AuthResponse,
    summary="GitHub OAuth Login",
)
async def github_login(
    payload: GitHubLoginRequest,
    db: Session = Depends(get_database),
):
    """
    Authenticate a user via GitHub OAuth.
    """
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
