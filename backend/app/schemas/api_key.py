from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Available Standard API Scopes
DEFAULT_SCOPES = ["read:projects", "read:profile"]
ALL_ALLOWED_SCOPES = {
    "read:projects",
    "write:projects",
    "read:profile",
    "write:profile",
    "read:organizations",
    "write:organizations",
    "read:messages",
    "full_access",
}


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=200, description="Friendly label for the API Key"
    )
    organization_id: Optional[uuid.UUID] = Field(
        None, description="Optional organization ID if creating an organization API Key"
    )
    scopes: List[str] = Field(
        default_factory=lambda: DEFAULT_SCOPES,
        description="List of assigned scopes/permissions",
    )
    expires_in_days: Optional[int] = Field(
        None, ge=1, le=365, description="Optional expiration period in days"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Optional explicit expiration datetime"
    )


class ApiKeyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    scopes: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    created_by_id: Optional[uuid.UUID] = None
    name: str
    prefix: str
    scopes: List[str]
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreateResponse(ApiKeyResponse):
    raw_key: str = Field(
        ...,
        description="The secret raw API key. IMPORTANT: Displayed ONCE upon creation/regeneration. Store it securely!",
    )


class PaginatedApiKeysResponse(BaseModel):
    items: List[ApiKeyResponse]
    total: int
    page: int
    limit: int
    pages: int
