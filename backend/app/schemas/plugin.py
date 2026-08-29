from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.plugin import PluginStatus, PluginType


class PluginManifestSchema(BaseModel):
    extension_points: list[str] = Field(
        default_factory=list,
        description="List of extension points (e.g. ['on_project_created', 'dashboard_widget', 'workflow_action'])",
    )
    webhook_url: Optional[str] = Field(
        default=None, description="HTTP webhook URL for asynchronous plugin events"
    )
    permissions: list[str] = Field(
        default_factory=list,
        description="Requested API permissions (e.g. ['read_projects', 'write_notifications'])",
    )
    widget_config: Optional[dict[str, Any]] = Field(
        default=None,
        description="UI Widget configuration (e.g. title, width, height, embed_url)",
    )
    config_schema: Optional[dict[str, Any]] = Field(
        default=None,
        description="JSON Schema for user/organization plugin setup options",
    )


class PluginCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Plugin name")
    slug: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
        description="URL-friendly slug (auto-generated if empty)",
    )
    description: str = Field(
        ...,
        min_length=5,
        description="Detailed plugin description and usage instructions",
    )
    version: str = Field(
        default="1.0.0", max_length=50, description="Plugin semver version string"
    )
    plugin_type: PluginType = Field(
        default=PluginType.INTEGRATION,
        description="Plugin type: integration, widget, workflow",
    )
    manifest: PluginManifestSchema = Field(
        ..., description="Extension manifest configuration"
    )


class PluginUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, min_length=5)
    version: Optional[str] = Field(default=None, max_length=50)
    manifest: Optional[PluginManifestSchema] = Field(default=None)
    status: Optional[PluginStatus] = Field(default=None)


class PluginResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str
    version: str
    author_id: uuid.UUID
    plugin_type: str
    status: str
    manifest: dict[str, Any]
    is_verified: bool = False
    is_official: bool = False
    install_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PluginInstallationCreate(BaseModel):
    organization_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional Organization ID for org-level plugin installation",
    )
    config: Optional[dict[str, Any]] = Field(
        default_factory=dict,
        description="Custom configuration settings for the installation",
    )


class PluginInstallationUpdate(BaseModel):
    is_enabled: Optional[bool] = Field(
        default=None, description="Enable or disable plugin execution"
    )
    config: Optional[dict[str, Any]] = Field(
        default=None, description="Updated custom configuration parameters"
    )


class PluginInstallationResponse(BaseModel):
    id: uuid.UUID
    plugin_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    is_enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    installed_at: datetime
    updated_at: datetime
    plugin: Optional[PluginResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PluginEventDispatch(BaseModel):
    event: str = Field(
        ..., description="Extension point event name (e.g., 'on_project_created')"
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Event data payload"
    )


class PluginDispatchItem(BaseModel):
    plugin_id: uuid.UUID
    plugin_slug: str
    installation_id: uuid.UUID
    has_webhook: bool = Field(
        default=False,
        description=(
            "Whether the plugin's manifest declares a webhook destination. "
            "The URL itself is not returned: an integration webhook is a "
            "bearer credential in practice, and a dispatch result does not "
            "need to repeat the destination to report what happened."
        ),
    )
    status: str = Field(
        description="Dispatch status: 'queued', 'skipped', 'no_webhook'"
    )


class PluginEventDispatchResult(BaseModel):
    event: str
    matched_plugins_count: int
    dispatched_installations_count: int
    dispatches: list[PluginDispatchItem]
