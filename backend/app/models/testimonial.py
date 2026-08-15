from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

MIN_BODY_LENGTH = 50
MAX_BODY_LENGTH = 2000

# The subject curates, they do not accumulate. Three featured testimonials fit
# above the fold; more and nobody reads any of them.
MAX_FEATURED = 3


class TestimonialRelationship(str, Enum):
    COLLABORATOR = "collaborator"
    MENTOR = "mentor"
    MENTEE = "mentee"
    CLIENT = "client"
    TEAMMATE = "teammate"


class TestimonialStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    HIDDEN = "hidden"


class Testimonial(Base):
    """
    A written recommendation one user leaves for another (#1044).

    Distinct from a skill endorsement (#257), which is a +1 on a tag. This is
    free text with an author, a stated relationship, and a moderation
    lifecycle the subject controls.
    """

    __tablename__ = "testimonials"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Parties
    # ==========================================================

    # Who the testimonial is about.
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Who wrote it.
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The collaboration it came out of, if any. SET NULL because the
    # testimonial is about the person, not the project.
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ==========================================================
    # Content
    # ==========================================================

    relationship_type: Mapped[TestimonialRelationship] = mapped_column(
        SqlEnum(TestimonialRelationship),
        name="relationship",
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ==========================================================
    # Moderation
    # ==========================================================

    status: Mapped[TestimonialStatus] = mapped_column(
        SqlEnum(TestimonialStatus),
        default=TestimonialStatus.PENDING,
        nullable=False,
        index=True,
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    # When the subject last acted on it (approved or hid it).
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    subject = relationship(
        "User", foreign_keys=[subject_id], backref="testimonials_received"
    )
    author = relationship(
        "User", foreign_keys=[author_id], backref="testimonials_written"
    )
    project = relationship("Project", backref="testimonials")

    # ==========================================================
    # Audit
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        # One testimonial per author, per subject. Someone with an opinion
        # worth stating twice can edit the one they already wrote.
        UniqueConstraint(
            "author_id", "subject_id", name="uq_testimonials_author_subject"
        ),
        # The public profile listing: one subject's approved testimonials.
        Index("ix_testimonials_subject_status", "subject_id", "status"),
        # The author's own "what have I written" view.
        Index("ix_testimonials_author_created", "author_id", "created_at"),
    )

    @property
    def relationship(self) -> TestimonialRelationship:
        """
        Alias for ``relationship_type``.

        The column is called ``relationship`` and that is what the API speaks,
        but the attribute cannot be -- ``relationship`` is SQLAlchemy's own
        name in this module's namespace. The mapped attribute carries the
        ``_type`` suffix and this property bridges the two.
        """
        return self.relationship_type

    def __repr__(self) -> str:
        return f"<Testimonial(subject={self.subject_id}, author={self.author_id}, status={self.status})>"
