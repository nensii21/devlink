from __future__ import annotations

import uuid

from datetime import datetime
import csv
import io
import structlog
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from app.models.audit_log import (
    AuditAction,
    AuditLog,
)
from app.middleware.audit_context import (
    audit_ip_address,
    audit_user_agent,
    audit_request_method,
    audit_request_path,
)

logger = structlog.get_logger("devlink.audit")


class AuditLogService:
    """
    Business logic for audit logging.
    """

    @staticmethod
    def create_log(
        db: Session,
        *,
        actor_id: uuid.UUID | None,
        action: AuditAction,
        entity_type: str,
        entity_id: str | None = None,
        target_user_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        metadata_info: dict | None = None,
        description: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_method: str | None = None,
        request_path: str | None = None,
        success: bool = True,
        status_code: int | None = None,
        error_message: str | None = None,
    ) -> AuditLog:

        def _sanitize_json(d: dict | None) -> dict | None:
            if not d:
                return d

            # A quick way to stringify complex objects like UUID or HttpUrl
            res = {}
            for k, v in d.items():
                if isinstance(v, (int, float, bool, str, type(None))):
                    res[k] = v
                elif isinstance(v, dict):
                    res[k] = _sanitize_json(v)
                elif isinstance(v, list):
                    res[k] = [
                        (
                            _sanitize_json(i)
                            if isinstance(i, dict)
                            else (
                                str(i)
                                if not isinstance(
                                    i, (int, float, bool, str, type(None))
                                )
                                else i
                            )
                        )
                        for i in v
                    ]
                else:
                    res[k] = str(v)
            return res

        resolved_ip = ip_address or audit_ip_address.get()
        resolved_ua = user_agent or audit_user_agent.get()
        resolved_method = request_method or audit_request_method.get()
        resolved_path = request_path or audit_request_path.get()

        log = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            target_user_id=target_user_id,
            project_id=project_id,
            organization_id=organization_id,
            old_values=_sanitize_json(old_values),
            new_values=_sanitize_json(new_values),
            metadata_info=_sanitize_json(metadata_info),
            description=description,
            ip_address=resolved_ip,
            user_agent=resolved_ua,
            request_method=resolved_method,
            request_path=resolved_path,
            success=success,
            status_code=status_code,
            error_message=error_message,
        )

        db.add(log)
        db.flush()
        db.refresh(log)

        logger.info(
            "audit_event",
            action=action.value,
            actor_id=str(actor_id) if actor_id else None,
            entity_type=entity_type,
            entity_id=entity_id,
            target_user_id=str(target_user_id) if target_user_id else None,
            project_id=str(project_id) if project_id else None,
            organization_id=str(organization_id) if organization_id else None,
            old_values=old_values,
            new_values=new_values,
            description=description,
            ip_address=resolved_ip,
            success=success,
            status_code=status_code,
        )

        return log

    @staticmethod
    def get_log(
        db: Session,
        log_id: uuid.UUID,
    ) -> AuditLog | None:

        return db.get(AuditLog, log_id)

    @staticmethod
    def list_logs(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        actor_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        action: AuditAction | None = None,
        entity_type: str | None = None,
    ) -> list[AuditLog]:

        stmt = select(AuditLog)

        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if project_id:
            stmt = stmt.where(AuditLog.project_id == project_id)
        if organization_id:
            stmt = stmt.where(AuditLog.organization_id == organization_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)

        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        return list(db.scalars(stmt))

    @staticmethod
    def list_actor_logs(
        db: Session,
        actor_id: uuid.UUID,
    ) -> list[AuditLog]:

        stmt = (
            select(AuditLog)
            .where(AuditLog.actor_id == actor_id)
            .order_by(AuditLog.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_project_logs(
        db: Session,
        project_id: uuid.UUID,
    ) -> list[AuditLog]:

        stmt = (
            select(AuditLog)
            .where(AuditLog.project_id == project_id)
            .order_by(AuditLog.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_organization_logs(
        db: Session,
        organization_id: uuid.UUID,
    ) -> list[AuditLog]:

        stmt = (
            select(AuditLog)
            .where(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_action_logs(
        db: Session,
        action: AuditAction,
    ) -> list[AuditLog]:

        stmt = (
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_failed_logs(
        db: Session,
    ) -> list[AuditLog]:

        stmt = (
            select(AuditLog)
            .where(AuditLog.success.is_(False))
            .order_by(AuditLog.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def delete_log(
        db: Session,
        log: AuditLog,
    ) -> None:

        db.delete(log)
        db.flush()

    @staticmethod
    def delete_actor_logs(
        db: Session,
        actor_id: uuid.UUID,
    ) -> None:

        stmt = select(AuditLog).where(AuditLog.actor_id == actor_id)

        logs = list(db.scalars(stmt))

        for log in logs:
            db.delete(log)

        db.flush()

    @staticmethod
    def search_org_audit_logs(
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        event_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        stmt = select(AuditLog).where(AuditLog.organization_id == organization_id)

        if user_id:
            stmt = stmt.where(
                or_(
                    AuditLog.actor_id == user_id,
                    AuditLog.target_user_id == user_id,
                )
            )

        if event_type:
            event_clean = event_type.strip().lower()
            stmt = stmt.where(func.lower(AuditLog.action).contains(event_clean))

        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)

        # Count total matches
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = db.scalar(count_stmt) or 0

        # Pagination
        offset = (page - 1) * limit
        paginated_stmt = (
            stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        )

        items = list(db.scalars(paginated_stmt))
        pages = (total_count + limit - 1) // limit if limit > 0 else 1

        return {
            "items": items,
            "total": total_count,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    @staticmethod
    def search_project_audit_logs(
        db: Session,
        project_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        event_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        stmt = select(AuditLog).where(AuditLog.project_id == project_id)

        if user_id:
            stmt = stmt.where(
                or_(
                    AuditLog.actor_id == user_id,
                    AuditLog.target_user_id == user_id,
                )
            )

        if event_type:
            event_clean = event_type.strip().lower()
            stmt = stmt.where(func.lower(AuditLog.action).contains(event_clean))

        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)

        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = db.scalar(count_stmt) or 0

        offset = (page - 1) * limit
        paginated_stmt = (
            stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        )

        items = list(db.scalars(paginated_stmt))
        pages = (total_count + limit - 1) // limit if limit > 0 else 1

        return {
            "items": items,
            "total": total_count,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    @staticmethod
    def export_org_audit_logs_csv(
        db: Session,
        organization_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        event_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
        search_result = AuditLogService.search_org_audit_logs(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            page=1,
            limit=10000,
        )
        logs = search_result["items"]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "ID",
                "Timestamp",
                "Action",
                "Actor ID",
                "Target User ID",
                "Entity Type",
                "Entity ID",
                "Description",
                "IP Address",
            ]
        )

        for log in logs:
            action_str = (
                log.action.value if hasattr(log.action, "value") else str(log.action)
            )
            writer.writerow(
                [
                    str(log.id),
                    log.created_at.isoformat() if log.created_at else "",
                    action_str,
                    str(log.actor_id) if log.actor_id else "",
                    str(log.target_user_id) if log.target_user_id else "",
                    log.entity_type or "",
                    str(log.entity_id) if log.entity_id else "",
                    log.description or "",
                    log.ip_address or "",
                ]
            )

        return output.getvalue()
