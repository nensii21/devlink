from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AuditAction(str, Enum):
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    EMAIL_CHANGED = "email_changed"

    # User
    PROFILE_UPDATED = "profile_updated"
    ACCOUNT_DELETED = "account_deleted"

    # Project
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"

    # Builder Flare
    BUILDER_FLARE_CREATED = "builder_flare_created"
    BUILDER_FLARE_UPDATED = "builder_flare_updated"
    BUILDER_FLARE_DELETED = "builder_flare_deleted"

    # Application
    APPLICATION_SUBMITTED = "application_submitted"
    APPLICATION_ACCEPTED = "application_accepted"
    APPLICATION_REJECTED = "application_rejected"

    # Repository
    REPOSITORY_CONNECTED = "repository_connected"
    REPOSITORY_SYNCED = "repository_synced"

    # Organization
    ORGANIZATION_CREATED = "organization_created"
    ORGANIZATION_UPDATED = "organization_updated"

    # Administration
    ROLE_CHANGED = "role_changed"
    USER_BANNED = "user_banned"
    USER_UNBANNED = "user_unbanned"

    # Security
    FAILED_LOGIN = "failed_login"
    TOKEN_REVOKED = "token_revoked"
    API_ACCESS = "api_access"


class AuditLog(Base):
    """
    Security audit log.
    """

    __tablename__ = "audit_logs"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # User
    # ==========================================================

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ==========================================================
    # Action
    # ==========================================================

    action: Mapped[AuditAction] = mapped_column(
        SqlEnum(AuditAction),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_id: Mapped[str | None] = mapped_column(
        String(100),
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    # ==========================================================
    # Request Information
    # ==========================================================

    ip_address: Mapped[str | None] = mapped_column(
        String(64),
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(512),
    )

    request_method: Mapped[str | None] = mapped_column(
        String(10),
    )

    request_path: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ==========================================================
    # Result
    # ==========================================================

    success: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    status_code: Mapped[int | None] = mapped_column()

    error_message: Mapped[str | None] = mapped_column(
        Text,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    user = relationship(
        "User",
        backref="audit_logs",
    )

    # ==========================================================
    # Audit
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<AuditLog(action='{self.action.value}', user={self.user_id})>"
