import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_current_user
from app.models.user import User
from app.schemas.org_audit_log import (
    OrgAuditLogPaginatedResponse,
    OrgAuditLogResponse,
    CreateOrgAuditLogRequest,
)
from app.services.audit_log_service import AuditLogService
from app.models.audit_log import AuditAction

router = APIRouter(
    prefix="/organizations/{org_id}/audit-logs",
    tags=["Organization Audit Logs"],
)


@router.get(
    "",
    response_model=OrgAuditLogPaginatedResponse,
    summary="List organization audit logs with search & pagination",
)
def get_organization_audit_logs(
    org_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(
        None, description="Filter by actor or target user ID"
    ),
    event_type: Optional[str] = Query(
        None,
        description="Filter by event action type e.g. member_invited, role_updated",
    ),
    start_date: Optional[datetime] = Query(
        None, description="Filter start date ISO timestamp"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter end date ISO timestamp"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Retrieve immutable organization audit log history with search filters and pagination."""
    return AuditLogService.search_org_audit_logs(
        db=db,
        organization_id=org_id,
        user_id=user_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )


@router.post(
    "",
    response_model=OrgAuditLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create immutable organization audit log record",
)
def create_organization_audit_log(
    org_id: uuid.UUID,
    payload: CreateOrgAuditLogRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Record an immutable organization audit event."""
    try:
        action_enum = AuditAction(payload.action.lower())
    except ValueError:
        # Fallback to ORGANIZATION_UPDATED if custom event name
        action_enum = AuditAction.ORGANIZATION_UPDATED

    target_uuid = None
    if payload.target_user_id:
        try:
            target_uuid = uuid.UUID(payload.target_user_id)
        except ValueError:
            pass

    log = AuditLogService.create_log(
        db=db,
        actor_id=current_user.id,
        action=action_enum,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        target_user_id=target_uuid,
        organization_id=org_id,
        description=payload.description
        or f"Action {payload.action} performed in organization",
        metadata_info=payload.metadata_info,
    )
    db.commit()
    return log


@router.get(
    "/export",
    summary="Export organization audit logs as CSV",
)
def export_organization_audit_logs_csv(
    org_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None),
    event_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """Export filtered organization audit logs as downloadable CSV data."""
    csv_data = AuditLogService.export_org_audit_logs_csv(
        db=db,
        organization_id=org_id,
        user_id=user_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
    )
    filename = f"org_audit_logs_{str(org_id)[:8]}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
