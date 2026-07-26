from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
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


class NotificationType(str, Enum):
    APPLICATION = "application"
    APPLICATION_ACCEPTED = "application_accepted"
    APPLICATION_REJECTED = "application_rejected"
    PROJECT_INVITE = "project_invite"
    PROJECT_UPDATE = "project_update"
    MESSAGE = "message"
    FOLLOW = "follow"
    MENTION = "mention"
    BUILDER_FLARE = "builder_flare"
    SYSTEM = "system"
    AI = "ai"


class Notification(Base):
    """
    User notification.
    """

    __tablename__ = "notifications"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # User
    # ==========================================================

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ==========================================================
    # Notification
    # ==========================================================

    type: Mapped[NotificationType] = mapped_column(
        SqlEnum(NotificationType),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    action_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ==========================================================
    # Related Resources
    # ==========================================================

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
    )

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
    )

    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
    )

    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
    )

    # ==========================================================
    # Status
    # ==========================================================

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    recipient = relationship(
        "User",
        foreign_keys=[recipient_id],
        backref="notifications",
    )

    sender = relationship(
        "User",
        foreign_keys=[sender_id],
    )

    project = relationship(
        "Project",
        backref="notifications",
    )

    conversation = relationship(
        "Conversation",
        backref="notifications",
    )

    chat_message = relationship(
        "Message",
        backref="notifications",
    )

    application = relationship(
        "Application",
        backref="notifications",
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
            f"<Notification(type='{self.type.value}', recipient={self.recipient_id})>"
        )
