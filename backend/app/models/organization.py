from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OrganizationType(str, Enum):
    COMPANY = "company"
    STARTUP = "startup"
    OPEN_SOURCE = "open_source"
    UNIVERSITY = "university"
    COMMUNITY = "community"


class Organization(Base):
    """
    Organization Model
    """

    __tablename__ = "organizations"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Owner
    # ==========================================================

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Basic Information
    # ==========================================================

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
    )

    slug: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    organization_type: Mapped[OrganizationType] = mapped_column(
        SqlEnum(OrganizationType),
        default=OrganizationType.STARTUP,
        nullable=False,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
    )

    # ==========================================================
    # Branding
    # ==========================================================

    logo_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    banner_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    location: Mapped[str | None] = mapped_column(
        String(200),
    )

    # ==========================================================
    # Social Links
    # ==========================================================

    github_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    linkedin_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    twitter_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ==========================================================
    # Statistics
    # ==========================================================

    members_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    projects_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    followers_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ==========================================================
    # Status
    # ==========================================================

    verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    hiring: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    owner = relationship(
        "User",
        backref="organizations",
    )

    # ==========================================================
    # Audit
    # ==========================================================

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

    def __repr__(self):
        return (
            f"<Organization(name='{self.name}', type='{self.organization_type.value}')>"
        )
