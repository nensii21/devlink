from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.models.user import User
from app.schemas.oauth_linking import (
    OAuthProvidersListResponse,
    LinkOAuthAccountRequest,
    UnlinkOAuthAccountRequest,
)
from app.services.oauth_linking_service import OAuthLinkingService

router = APIRouter(
    tags=["OAuth Account Linking"],
)


@router.get(
    "/users/me/oauth-accounts",
    response_model=OAuthProvidersListResponse,
    summary="List connected OAuth providers",
)
@router.get(
    "/auth/oauth/providers",
    response_model=OAuthProvidersListResponse,
    summary="List connected OAuth providers (Alias)",
)
def get_linked_oauth_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    return OAuthLinkingService.get_linked_providers(db, current_user)


@router.post(
    "/users/me/oauth-accounts/link",
    response_model=OAuthProvidersListResponse,
    summary="Link OAuth provider account",
)
@router.post(
    "/auth/oauth/link",
    response_model=OAuthProvidersListResponse,
    summary="Link OAuth provider account (Alias)",
)
def link_oauth_account(
    payload: LinkOAuthAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    return OAuthLinkingService.link_oauth_account(
        db,
        user=current_user,
        provider=payload.provider,
        provider_user_id=payload.provider_user_id,
    )


@router.post(
    "/users/me/oauth-accounts/unlink",
    response_model=OAuthProvidersListResponse,
    summary="Unlink OAuth provider account",
)
@router.post(
    "/auth/oauth/unlink",
    response_model=OAuthProvidersListResponse,
    summary="Unlink OAuth provider account (Alias)",
)
def unlink_oauth_account(
    payload: UnlinkOAuthAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    return OAuthLinkingService.unlink_oauth_account(
        db,
        user=current_user,
        provider=payload.provider,
    )


@router.delete(
    "/users/me/oauth-accounts/{provider}",
    response_model=OAuthProvidersListResponse,
    summary="Unlink OAuth provider by path",
)
def unlink_oauth_account_by_path(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    return OAuthLinkingService.unlink_oauth_account(
        db,
        user=current_user,
        provider=provider,
    )
