"""SQLAlchemy models for project onboarding checklists.

Provides structured onboarding flows for new project members with
trackable checklist items, completion status, and reusable templates.
"""

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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ChecklistItemType(str, Enum):
    TASK = "task"
    READ = "read"
    WATCH = "watch"
    MEETING = "meeting"
    SUBMIT = "submit"
    CONFIGURE = "configure"


class OnboardingChecklist(Base):
    """A checklist template that can be applied to project members."""

    __tablename__ = "onboarding_checklists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items = relationship(
        "OnboardingItem",
        back_populates="checklist",
        cascade="all, delete-orphan",
        order_by="OnboardingItem.order",
    )
    assignments = relationship(
        "OnboardingAssignment",
        back_populates="checklist",
        cascade="all, delete-orphan",
    )


class OnboardingItem(Base):
    """A single step in an onboarding checklist."""

    __tablename__ = "onboarding_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    checklist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("onboarding_checklists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    item_type: Mapped[ChecklistItemType] = mapped_column(
        SqlEnum(ChecklistItemType), default=ChecklistItemType.TASK, nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    resource_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    checklist = relationship("OnboardingChecklist", back_populates="items")


class OnboardingAssignment(Base):
    """Tracks which user has been assigned which checklist and their progress."""

    __tablename__ = "onboarding_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    checklist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("onboarding_checklists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    checklist = relationship("OnboardingChecklist", back_populates="assignments")
    item_completions = relationship(
        "OnboardingItemCompletion",
        back_populates="assignment",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "checklist_id", "user_id", name="uq_checklist_user_assignment"
        ),
    )


class OnboardingItemCompletion(Base):
    """Records that a user completed a specific onboarding item."""

    __tablename__ = "onboarding_item_completions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("onboarding_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("onboarding_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assignment = relationship("OnboardingAssignment", back_populates="item_completions")

    __table_args__ = (
        UniqueConstraint(
            "assignment_id", "item_id", name="uq_assignment_item_completion"
        ),
    )
