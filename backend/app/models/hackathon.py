from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class HackathonStatus(str, Enum):
    DRAFT = "draft"
    REGISTRATION_OPEN = "registration_open"
    IN_PROGRESS = "in_progress"
    JUDGING = "judging"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Hackathon(Base):
    """
    A hackathon event.
    """

    __tablename__ = "hackathons"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Organizer
    # ==========================================================

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Details
    # ==========================================================

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    theme: Mapped[str | None] = mapped_column(
        String(200),
    )

    # ==========================================================
    # Dates
    # ==========================================================

    registration_starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    registration_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # ==========================================================
    # Rules
    # ==========================================================

    min_team_size: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    max_team_size: Mapped[int] = mapped_column(
        Integer,
        default=4,
        nullable=False,
    )

    # ==========================================================
    # Metadata
    # ==========================================================

    prize: Mapped[str | None] = mapped_column(
        String(300),
    )

    website_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ==========================================================
    # Status
    # ==========================================================

    status: Mapped[HackathonStatus] = mapped_column(
        SqlEnum(HackathonStatus),
        default=HackathonStatus.DRAFT,
        nullable=False,
        index=True,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    creator = relationship(
        "User",
        backref="hackathons",
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

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Hackathon(" f"name='{self.name}', " f"status='{self.status.value}'" f")>"
        )
