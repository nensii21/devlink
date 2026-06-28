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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ConversationType(str, Enum):
    DIRECT = "direct"
    PROJECT = "project"
    GROUP = "group"
    AI = "ai"


class Conversation(Base):
    """
    Conversation Model
    """

    __tablename__ = "conversations"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Conversation Details
    # ==========================================================

    type: Mapped[ConversationType] = mapped_column(
        SqlEnum(ConversationType),
        default=ConversationType.DIRECT,
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
    )

    # ==========================================================
    # Related Project
    # ==========================================================

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Status
    # ==========================================================

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    creator = relationship(
        "User",
        backref="created_conversations",
    )

    project = relationship(
        "Project",
        backref="conversations",
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
        return f"<Conversation(" f"type='{self.type.value}', " f"id={self.id}" f")>"
