from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AuditAction(str, Enum):
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    EMAIL_CHANGED = "email_changed"

    # User Profile
    PROFILE_UPDATED = "profile_updated"
    AVATAR_CHANGED = "avatar_changed"
    ACCOUNT_DELETED = "account_deleted"

    # Roles / Admin
    USER_PROMOTED = "user_promoted"
    USER_DEMOTED = "user_demoted"
    ADMIN_ASSIGNED = "admin_assigned"
    ADMIN_REMOVED = "admin_removed"
    PERMISSIONS_CHANGED = "permissions_changed"
    ROLE_CHANGED = "role_changed"
    USER_SUSPENDED = "user_suspended"
    USER_ACTIVATED = "user_activated"
    USER_BANNED = "user_banned"
    USER_UNBANNED = "user_unbanned"
    USER_EMAIL_VERIFIED = "user_email_verified"
    SETTINGS_CHANGED = "settings_changed"

    # Project
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_TITLE_UPDATED = "project_title_updated"
    PROJECT_DESCRIPTION_UPDATED = "project_description_updated"
    PROJECT_STATUS_CHANGED = "project_status_changed"
    PROJECT_MEMBER_ADDED = "project_member_added"
    PROJECT_MEMBER_REMOVED = "project_member_removed"
    PROJECT_MEMBER_ROLE_UPDATED = "project_member_role_updated"
    PROJECT_OWNERSHIP_TRANSFERRED = "project_ownership_transferred"
    PROJECT_ARCHIVED = "project_archived"
    PROJECT_RESTORED = "project_restored"
    PROJECT_DELETED = "project_deleted"
    PROJECT_VERSION_CREATED = "project_version_created"
    PROJECT_VERSION_RESTORED = "project_version_restored"

    # Invitations
    INVITATION_SENT = "invitation_sent"
    INVITATION_ACCEPTED = "invitation_accepted"
    INVITATION_REJECTED = "invitation_rejected"
    INVITATION_EXPIRED = "invitation_expired"
    INVITATION_REVOKED = "invitation_revoked"

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
    ORGANIZATION_DELETED = "organization_deleted"
    MEMBER_INVITED = "member_invited"
    MEMBER_REMOVED = "member_removed"
    ROLE_UPDATED = "role_updated"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_REGENERATED = "api_key_regenerated"
    API_KEY_UPDATED = "api_key_updated"

    # Security
    FAILED_LOGIN = "failed_login"
    SUSPICIOUS_LOGIN_ATTEMPT = "suspicious_login_attempt"
    TOKEN_REVOKED = "token_revoked"
    API_ACCESS = "api_access"
    API_TOKEN_CREATED = "api_token_created"
    API_TOKEN_REVOKED = "api_token_revoked"


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
    # Actor / Target References
    # ==========================================================

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ==========================================================
    # Action & Entity
    # ==========================================================

    action: Mapped[AuditAction] = mapped_column(
        SqlEnum(AuditAction),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    entity_id: Mapped[str | None] = mapped_column(
        String(100),
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    # ==========================================================
    # Changes & Metadata (JSON)
    # ==========================================================

    old_values: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON, "sqlite")
    )
    new_values: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON, "sqlite")
    )
    metadata_info: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON, "sqlite")
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

    actor = relationship(
        "User",
        foreign_keys=[actor_id],
        backref="performed_audit_logs",
    )

    target_user = relationship(
        "User",
        foreign_keys=[target_user_id],
        backref="targeted_audit_logs",
    )

    project = relationship(
        "Project",
        foreign_keys=[project_id],
        backref="audit_logs",
    )

    organization = relationship(
        "Organization",
        foreign_keys=[organization_id],
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
        return f"<AuditLog(action='{self.action.value}', actor={self.actor_id})>"
