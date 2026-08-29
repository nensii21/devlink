"""
API key routes.

A key belongs either to a user or to an organisation, never both. The routes
below are shared by the two shapes: there are no organisation-scoped read,
update, regenerate or revoke routes, so an organisation key is managed through
`/api/api-keys/{key_id}` like any other.

That is why every one of them delegates the ownership decision to
`ApiKeyService.assert_can_manage` rather than checking `key.user_id` inline.
The inline version short-circuited on organisation keys -- where `user_id` is
NULL -- and let any authenticated caller regenerate someone else's
organisation secret and be handed the plaintext.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.core.rbac import ORG_MANAGE_TOKENS
from app.dependencies import get_current_user, get_database, require_org_permission
from app.models.api_key import ApiKey
from app.models.user import User
from app.schemas.api_key import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyResponse,
    ApiKeyUpdateRequest,
    PaginatedApiKeysResponse,
)
from app.services.api_key_service import ApiKeyService

router = APIRouter(
    prefix="/api-keys",
    tags=["API Key Management"],
)

api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


# ---------------------------------------------------------------------------
# API Key Authentication Dependency
# ---------------------------------------------------------------------------


def verify_api_key(
    scope: Optional[str] = None,
):
    """Dependency factory to authenticate requests using X-API-Key or Authorization Bearer header."""

    def _dependency(
        x_api_key: Optional[str] = Security(api_key_header_scheme),
        authorization: Optional[str] = Header(None),
        db: Session = Depends(get_database),
    ) -> ApiKey:
        raw_key = x_api_key
        if (
            not raw_key
            and authorization
            and authorization.lower().startswith("bearer dlk_live_")
        ):
            raw_key = authorization.split(" ", 1)[1]

        if not raw_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-API-Key or Bearer API token header",
            )

        return ApiKeyService.authenticate_api_key(
            db, raw_key=raw_key, required_scope=scope
        )

    return _dependency


# ---------------------------------------------------------------------------
# Personal User API Keys Endpoints (#605)
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API Key",
    description="Generate a secure API key for integrating third-party tools. The raw_key secret is displayed ONLY ONCE upon creation.",
)
def create_api_key(
    payload: ApiKeyCreateRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> ApiKeyCreateResponse:
    raw_key, api_key = ApiKeyService.create_api_key(
        db, actor=current_user, payload=payload
    )

    data = ApiKeyResponse.model_validate(api_key).model_dump()
    data["raw_key"] = raw_key
    return ApiKeyCreateResponse(**data)


@router.get(
    "/",
    response_model=PaginatedApiKeysResponse,
    summary="List API Keys",
    description="Retrieve paginated list of API keys owned by the current user.",
)
def list_api_keys(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    include_revoked: bool = Query(
        False,
        description="Include keys that have been revoked. Off by default.",
    ),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> PaginatedApiKeysResponse:
    res = ApiKeyService.list_api_keys(
        db,
        user_id=current_user.id,
        page=page,
        limit=limit,
        include_revoked=include_revoked,
    )
    items = [ApiKeyResponse.model_validate(k) for k in res["items"]]
    return PaginatedApiKeysResponse(
        items=items,
        total=res["total"],
        page=res["page"],
        limit=res["limit"],
        pages=res["pages"],
    )


@router.get(
    "/{key_id}",
    response_model=ApiKeyResponse,
    summary="Get API Key Details",
    description=(
        "Retrieve metadata for a specific API key. Personal keys are readable "
        "by their owner; organisation keys by anyone holding "
        "`org:manage_tokens` in that organisation."
    ),
)
def get_api_key(
    key_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> ApiKeyResponse:
    # This route used to carry its own copy of the ownership condition, and
    # the copy had the same short-circuit bug as the three in the service.
    # One helper, one place to get it wrong.
    key = ApiKeyService.get_manageable_api_key(db, key_id, current_user)
    return ApiKeyResponse.model_validate(key)


@router.patch(
    "/{key_id}",
    response_model=ApiKeyResponse,
    summary="Update API Key",
    description="Update API key label name, assigned permission scopes, or expiration date.",
)
def update_api_key(
    key_id: uuid.UUID,
    payload: ApiKeyUpdateRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> ApiKeyResponse:
    key = ApiKeyService.update_api_key(
        db, key_id=key_id, payload=payload, actor=current_user
    )
    return ApiKeyResponse.model_validate(key)


@router.post(
    "/{key_id}/regenerate",
    response_model=ApiKeyCreateResponse,
    summary="Regenerate API Key Secret",
    description="Invalidate current API key secret and generate a new token string. The new raw_key is displayed ONLY ONCE.",
)
def regenerate_api_key(
    key_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> ApiKeyCreateResponse:
    raw_key, api_key = ApiKeyService.regenerate_api_key(
        db, key_id=key_id, actor=current_user
    )

    data = ApiKeyResponse.model_validate(api_key).model_dump()
    data["raw_key"] = raw_key
    return ApiKeyCreateResponse(**data)


@router.post(
    "/{key_id}/revoke",
    response_model=ApiKeyResponse,
    summary="Revoke API Key (POST)",
    description="Revoke an API key immediately.",
)
@router.delete(
    "/{key_id}",
    response_model=ApiKeyResponse,
    summary="Revoke API Key (DELETE)",
    description="Revoke an API key immediately.",
)
def revoke_api_key(
    key_id: uuid.UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> ApiKeyResponse:
    key = ApiKeyService.revoke_api_key(db, key_id=key_id, actor=current_user)
    return ApiKeyResponse.model_validate(key)


# ---------------------------------------------------------------------------
# Organization API Keys Endpoints (#605)
# ---------------------------------------------------------------------------

org_api_keys_router = APIRouter(
    prefix="/organizations/{organization_id}/api-keys",
    tags=["Organization API Keys"],
)


@org_api_keys_router.post(
    "/",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_org_permission(ORG_MANAGE_TOKENS))],
    summary="Create Organization API Key",
)
def create_org_api_key(
    organization_id: uuid.UUID,
    payload: ApiKeyCreateRequest,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
) -> ApiKeyCreateResponse:
    payload.organization_id = organization_id
    raw_key, api_key = ApiKeyService.create_api_key(
        db, actor=current_user, payload=payload
    )

    data = ApiKeyResponse.model_validate(api_key).model_dump()
    data["raw_key"] = raw_key
    return ApiKeyCreateResponse(**data)


@org_api_keys_router.get(
    "/",
    response_model=PaginatedApiKeysResponse,
    dependencies=[Depends(require_org_permission(ORG_MANAGE_TOKENS))],
    summary="List Organization API Keys",
)
def list_org_api_keys(
    organization_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    include_revoked: bool = Query(
        False,
        description="Include keys that have been revoked. Off by default.",
    ),
    db: Session = Depends(get_database),
) -> PaginatedApiKeysResponse:
    res = ApiKeyService.list_api_keys(
        db,
        organization_id=organization_id,
        page=page,
        limit=limit,
        include_revoked=include_revoked,
    )
    items = [ApiKeyResponse.model_validate(k) for k in res["items"]]
    return PaginatedApiKeysResponse(
        items=items,
        total=res["total"],
        page=res["page"],
        limit=res["limit"],
        pages=res["pages"],
    )
