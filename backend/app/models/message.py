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
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    AI = "ai"


class Message(Base):
    """
    Chat message.
    """

    __tablename__ = "messages"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    parent_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ==========================================================
    # Message
    # ==========================================================

    type: Mapped[MessageType] = mapped_column(
        SqlEnum(MessageType),
        default=MessageType.TEXT,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    attachment_url: Mapped[str | None] = mapped_column(
        String(500),
    )

    attachment_name: Mapped[str | None] = mapped_column(
        String(255),
    )

    attachment_size: Mapped[int | None] = mapped_column()

    mime_type: Mapped[str | None] = mapped_column(
        String(100),
    )

    # ==========================================================
    # Status
    # ==========================================================

    is_edited: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    conversation = relationship(
        "Conversation",
        backref="messages",
    )

    sender = relationship(
        "User",
        backref="messages",
    )

    parent_message = relationship(
        "Message",
        remote_side=[id],
        backref="replies",
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

    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self):
        return (
            f"<Message("
            f"id={self.id}, "
            f"type='{self.type.value}'"
            f")>"
        )