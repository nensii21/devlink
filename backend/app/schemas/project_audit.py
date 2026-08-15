from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectAuditLogResponse(BaseModel):
    id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    target_user_id: Optional[uuid.UUID] = None
    project_id: uuid.UUID
    action: str = Field(
        ...,
        description="Audit action name (e.g. project_created, project_title_updated, project_member_added)",
    )
    entity_type: str = "project"
    entity_id: str
    old_values: Optional[dict[str, Any]] = None
    new_values: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedProjectAuditLogsResponse(BaseModel):
    items: list[ProjectAuditLogResponse]
    total: int
    page: int
    limit: int
    pages: int
