"""
API Router for DevLink Plugin & Extension System (#582)
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_active_user, get_database
from app.models.plugin import PluginStatus, PluginType
from app.models.user import User
from app.schemas.plugin import (
    PluginCreate,
    PluginEventDispatch,
    PluginEventDispatchResult,
    PluginInstallationCreate,
    PluginInstallationResponse,
    PluginInstallationUpdate,
    PluginResponse,
    PluginUpdate,
)
from app.services.plugin_service import PluginService

router = APIRouter(
    prefix="/plugins",
    tags=["Plugin & Extension System"],
)


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Ensure current user is a system admin."""
    if (
        getattr(current_user, "system_role", None) != "admin"
        and getattr(current_user, "role", None) != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action.",
        )
    return current_user


# ------------------------------------------------------------------
# Plugin Marketplace & Registry Endpoints
# ------------------------------------------------------------------


@router.get(
    "",
    response_model=dict[str, Any],
    summary="List Marketplace Plugins",
    description="Browse and search available plugins, widgets, and workflow extensions.",
)
@router.get(
    "/",
    response_model=dict[str, Any],
    include_in_schema=False,
)
def list_plugins(
    plugin_type: Optional[PluginType] = Query(
        None, description="Filter by plugin type: integration, widget, workflow"
    ),
    status_filter: Optional[PluginStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status"),
    search: Optional[str] = Query(
        None, description="Search name, slug, or description"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_database),
) -> dict[str, Any]:
    plugins, total = PluginService.list_plugins(
        db,
        plugin_type=plugin_type,
        status_filter=status_filter,
        is_verified=is_verified,
        search=search,
        page=page,
        limit=limit,
    )

    items = [PluginResponse.model_validate(p) for p in plugins]
    pages = (total + limit - 1) // limit if limit > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.post(
    "",
    response_model=PluginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Plugin or Extension",
    description="Register a custom integration, widget, or workflow plugin with extension manifest payload.",
)
@router.post(
    "/",
    response_model=PluginResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_plugin(
    plugin_in: PluginCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> PluginResponse:
    plugin = PluginService.create_plugin(db, plugin_in=plugin_in, author=current_user)
    return PluginResponse.model_validate(plugin)


@router.get(
    "/installed/me",
    response_model=list[PluginInstallationResponse],
    summary="List User Installed Plugins",
    description="Retrieve all plugins installed for the current developer or specified organization.",
)
def list_installed_plugins(
    organization_id: Optional[uuid.UUID] = Query(
        None, description="Optional Organization ID filter"
    ),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> list[PluginInstallationResponse]:
    installations = PluginService.list_user_installations(
        db, user=current_user, organization_id=organization_id
    )
    return [PluginInstallationResponse.model_validate(inst) for inst in installations]


@router.post(
    "/dispatch-event",
    response_model=PluginEventDispatchResult,
    summary="Dispatch Plugin Extension Event (administrators only)",
    description=(
        "Trigger an extension point event across active and enabled plugin "
        "integrations. This is a platform-internal fan-out primitive: it "
        "enumerates every enabled installation on the platform, not just the "
        "caller's, so it is restricted to administrators."
    ),
)
def dispatch_plugin_event(
    event_in: PluginEventDispatch,
    db: Session = Depends(get_database),
    _actor: User = Depends(require_admin),
) -> PluginEventDispatchResult:
    return PluginService.dispatch_event(
        db, event=event_in.event, payload=event_in.payload
    )


@router.get(
    "/{plugin_id_or_slug}",
    response_model=PluginResponse,
    summary="Get Plugin details and manifest",
)
def get_plugin(
    plugin_id_or_slug: str,
    db: Session = Depends(get_database),
) -> PluginResponse:
    plugin = PluginService.get_plugin_or_404(db, plugin_id_or_slug)
    return PluginResponse.model_validate(plugin)


@router.patch(
    "/{plugin_id}",
    response_model=PluginResponse,
    summary="Update Plugin manifest or details",
)
def update_plugin(
    plugin_id: uuid.UUID,
    plugin_in: PluginUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> PluginResponse:
    plugin = PluginService.update_plugin(
        db, plugin_id=plugin_id, plugin_in=plugin_in, actor=current_user
    )
    return PluginResponse.model_validate(plugin)


@router.post(
    "/{plugin_id}/install",
    response_model=PluginInstallationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Install Plugin",
    description="Install a plugin for the authenticated user or organization.",
)
def install_plugin(
    plugin_id: uuid.UUID,
    install_in: Optional[PluginInstallationCreate] = None,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> PluginInstallationResponse:
    payload = install_in or PluginInstallationCreate()
    installation = PluginService.install_plugin(
        db, plugin_id=plugin_id, user=current_user, install_in=payload
    )
    return PluginInstallationResponse.model_validate(installation)


@router.delete(
    "/{plugin_id}/install",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Uninstall Plugin",
)
def uninstall_plugin(
    plugin_id: uuid.UUID,
    organization_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    PluginService.uninstall_plugin(
        db, plugin_id=plugin_id, user=current_user, organization_id=organization_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/installations/{installation_id}",
    response_model=PluginInstallationResponse,
    summary="Update Plugin Installation settings",
    description="Enable/disable plugin execution or update custom setup settings.",
)
def update_installation(
    installation_id: uuid.UUID,
    update_in: PluginInstallationUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
) -> PluginInstallationResponse:
    installation = PluginService.update_installation(
        db, installation_id=installation_id, update_in=update_in, user=current_user
    )
    return PluginInstallationResponse.model_validate(installation)


@router.post(
    "/{plugin_id}/verify",
    response_model=PluginResponse,
    summary="Verify Plugin (Admin Only)",
)
def verify_plugin(
    plugin_id: uuid.UUID,
    is_verified: bool = Query(True),
    is_official: bool = Query(False),
    db: Session = Depends(get_database),
    _: User = Depends(require_admin),
) -> PluginResponse:
    plugin = PluginService.verify_plugin(
        db, plugin_id=plugin_id, is_verified=is_verified, is_official=is_official
    )
    return PluginResponse.model_validate(plugin)
