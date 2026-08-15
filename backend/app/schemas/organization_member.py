from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.organization_member import OrgMemberRole


class OrganizationMemberBase(BaseModel):
    role: OrgMemberRole


class OrganizationMemberUpdate(BaseModel):
    role: OrgMemberRole


class OrganizationMemberResponse(OrganizationMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool
    joined_at: datetime
    created_at: datetime
    updated_at: datetime
