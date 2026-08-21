from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserRole(str, Enum):
    """Application-level user role."""

    USER = "user"
    ADMIN = "admin"
    DEVELOPER = "developer"
    MEMBER = "member"
    VIEWER = "viewer"
    MODERATOR = "moderator"


class User(Base):
    """
    DevLink User Model
    """

    __tablename__ = "users"

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Basic Information
    # ------------------------------------------------------------------

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    reputation_score: Mapped[int] = mapped_column(
        default=0,
        index=True,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

    badges: Mapped[list[str]] = mapped_column(
        ARRAY(String).with_variant(JSON, "sqlite"),
        default=list,
        # '{}' is the empty-array literal for a Postgres text[]. This said
        # '[]', which Postgres rejects outright:
        #
        #     psycopg.errors.InvalidTextRepresentation:
        #     malformed array literal: "[]"
        #
        # so Base.metadata.create_all() could not build the schema on Postgres
        # at all. It went unnoticed because the tests create_all against
        # SQLite, where this column is JSON and '[]' is valid.
        #
        # The migration that adds the column (1a2b3c4d5e6f) already uses '{}',
        # so this aligns the model with the schema that actually exists rather
        # than changing it.
        server_default="{}",
        nullable=False,
    )

    headline: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    profile_image: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    cover_image: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    video_introduction_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    video_introduction_thumbnail_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    timezone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    availability: Mapped[list] = mapped_column(
        JSON,
        nullable=True,
        default=list,
    )

    website: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resume_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    voice_introduction_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    portfolio_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    public_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    github_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    linkedin_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    twitter_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Professional
    # ------------------------------------------------------------------

    role: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    experience_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    company: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    experience: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    education: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    certifications: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    open_to_work: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    collaboration_status: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        default="available",
        server_default="available",
    )

    is_private: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    privacy_settings: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=lambda: {
            "email": "private",
            "github": "public",
            "resume": "public",
            "social_links": "public",
            "availability": "public",
            "activity": "public",
        },
    )

    def get_privacy_settings(self) -> dict:
        defaults = {
            "email": "private",
            "github": "public",
            "resume": "public",
            "social_links": "public",
            "availability": "public",
            "activity": "public",
        }
        if not self.privacy_settings:
            return defaults
        res = dict(defaults)
        res.update(self.privacy_settings)
        return res

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Multi-Factor Authentication (MFA)
    # ------------------------------------------------------------------

    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    mfa_secret: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    mfa_backup_codes: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # System-level RBAC role (issue #357).
    # Controls platform-wide permissions independent of org/project membership.
    # Values: admin, maintainer, organization_owner, project_owner, contributor, user
    system_role: Mapped[str] = mapped_column(
        String(50),
        default="user",
        nullable=False,
        index=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(20), default="unverified", nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=True,
    )
    # ------------------------------------------------------------------
    # OAuth
    # ------------------------------------------------------------------

    microsoft_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
    )

    github_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
    )

    google_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
    )

    linkedin_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
    )

    gitlab_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
    )

    # ------------------------------------------------------------------
    # Soft Delete
    # ------------------------------------------------------------------

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    deleted_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[deleted_by_id],
        remote_side="User.id",
    )

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_online(self) -> bool:
        """
        Check if the user is currently online.

        Returns True if the user was active within the online threshold
        (defaults to 300 seconds, customizable via _online_threshold).
        """
        if not self.last_seen:
            return False
        threshold = getattr(self, "_online_threshold", 300)
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        last_seen = self.last_seen
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        return (now - last_seen).total_seconds() < threshold

    @property
    def skills(self) -> list[str]:
        try:
            if not hasattr(self, "user_skills") or not self.user_skills:
                return []
            return [us.skill.name for us in self.user_skills if getattr(us, "skill", None)]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', email='{self.email}')>"


