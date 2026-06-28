from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import (
    AuditAction,
    AuditLog,
)


class AuditLogService:
    """
    Business logic for audit logging.
    """

    @staticmethod
    def create_log(
        db: Session,
        *,
        user_id: uuid.UUID | None,
        action: AuditAction,
        resource_type: str,
        resource_id: str | None = None,
        description: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_method: str | None = None,
        request_path: str | None = None,
        success: bool = True,
        status_code: int | None = None,
        error_message: str | None = None,
    ) -> AuditLog:

        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            success=success,
            status_code=status_code,
            error_message=error_message,
        )

        db.add(log)
        db.commit()
        db.refresh(log)

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
    ) -> list[AuditLog]:

        stmt = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(db.scalars(stmt))

    @staticmethod
    def list_user_logs(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[AuditLog]:

        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
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
        db.commit()

    @staticmethod
    def delete_user_logs(
        db: Session,
        user_id: uuid.UUID,
    ) -> None:

        stmt = select(AuditLog).where(AuditLog.user_id == user_id)

        logs = list(db.scalars(stmt))

        for log in logs:
            db.delete(log)

        db.commit()
