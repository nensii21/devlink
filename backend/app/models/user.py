from __future__ import annotations


import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    String,
    Text,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


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

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

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

    open_to_work: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

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

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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
    DateTime(timezone=True),
    nullable=True,
    )

    last_active_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
        DateTime, default=datetime.utcnow, nullable=True
    )
        DateTime(timezone=True),
        nullable=True,
    )

    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=True
    )
    # ------------------------------------------------------------------
    # OAuth
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<User(" f"username='{self.username}', " f"email='{self.email}'" f")>"
