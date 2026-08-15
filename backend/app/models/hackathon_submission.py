from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
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


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class HackathonSubmission(Base):
    """
    A team's project submission for a hackathon.
    """

    __tablename__ = "hackathon_submissions"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Foreign Keys
    # ==========================================================

    hackathon_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hackathons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hackathon_teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Submission Details
    # ==========================================================

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    repo_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    demo_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ==========================================================
    # Status
    # ==========================================================

    status: Mapped[SubmissionStatus] = mapped_column(
        SqlEnum(SubmissionStatus),
        default=SubmissionStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    hackathon = relationship(
        "Hackathon",
        backref="submissions",
    )

    team = relationship(
        "HackathonTeam",
        backref="submissions",
    )

    submitter = relationship(
        "User",
        backref="hackathon_submissions",
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

    def __repr__(self) -> str:
        return (
            f"<HackathonSubmission(title='{self.title}', status='{self.status.value}')>"
        )
