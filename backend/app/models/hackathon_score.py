from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class HackathonScore(Base):
    """
    A judge's score for a submission.
    """

    __tablename__ = "hackathon_scores"

    __table_args__ = (
        UniqueConstraint(
            "submission_id",
            "judge_id",
            name="uq_hackathon_score",
        ),
    )

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

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hackathon_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    judge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hackathon_judges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Score
    # ==========================================================

    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    comments: Mapped[str | None] = mapped_column(
        Text,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    submission = relationship(
        "HackathonSubmission",
        backref="scores",
    )

    judge = relationship(
        "HackathonJudge",
        backref="scores",
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
            f"<HackathonScore(submission_id={self.submission_id}, score={self.score})>"
        )
