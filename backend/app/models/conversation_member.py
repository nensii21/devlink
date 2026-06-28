from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ConversationRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class ConversationMember(Base):
    """
    Users participating in a conversation.
    """

    __tablename__ = "conversation_members"

    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "user_id",
            name="uq_conversation_member",
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

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Membership
    # ==========================================================

    role: Mapped[ConversationRole] = mapped_column(
        SqlEnum(ConversationRole),
        default=ConversationRole.MEMBER,
        nullable=False,
    )

    is_muted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    conversation = relationship(
        "Conversation",
        backref="members",
    )

    user = relationship(
        "User",
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
        return (
            f"<ConversationMember("
            f"conversation={self.conversation_id}, "
            f"user={self.user_id}"
            f")>"
        )