from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.models.user import User
from app.models.audit_log import AuditAction
from app.services.audit_log_service import AuditLogService
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    target_user_id: uuid.UUID | None
    project_id: uuid.UUID | None
    organization_id: uuid.UUID | None
    action: AuditAction
    entity_type: str
    entity_id: str | None
    description: str | None
    old_values: dict | None
    new_values: dict | None
    metadata_info: dict | None
    ip_address: str | None
    user_agent: str | None
    request_method: str | None
    request_path: str | None
    success: bool
    status_code: int | None
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get(
    "/",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    actor_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    action: AuditAction | None = None,
    entity_type: str | None = None,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    # Only superadmins or similar roles should ideally query all logs.
    # For now we'll just return the logs.
    return AuditLogService.list_logs(
        db,
        skip=skip,
        limit=limit,
        actor_id=actor_id,
        project_id=project_id,
        organization_id=organization_id,
        action=action,
        entity_type=entity_type,
    )
